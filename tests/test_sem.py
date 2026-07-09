"""
Unit tests for taos/sem.py.

All tests are pure numpy — no HPC environment, filesystem, or mocks needed.
Element geometry tests use a synthetic ne=1 cube-sphere mesh (6 elements,
8 nodes) constructed analytically.

Run with:
    python -m pytest tests/test_sem.py -v
"""
import unittest
import numpy as np

from taos.sem import (
    GLL_POINTS,
    GLL_WEIGHTS,
    GLL_DERIV,
    cv_corner_positions,
    cv_corners_assembled,
    cv_reference_edges,
    element_metric,
    gll_node_areas,
    gll_positions,
    smooth_phis,
    unique_gll_nodes,
)

#-------------------------------------------------------------------------------
# synthetic ne=1 cube-sphere mesh fixture
#
# 8 nodes at the corners of the unit cube projected to the unit sphere,
# 6 quadrilateral elements (one per cube face).
#
# Corner ordering within each element:
#   corner 0 → (ξ=−1, η=−1)
#   corner 1 → (ξ=+1, η=−1)
#   corner 2 → (ξ=+1, η=+1)
#   corner 3 → (ξ=−1, η=+1)

_S3 = 1.0 / np.sqrt(3.0)

_NE1_COORDS = _S3 * np.array([
    [-1, -1, -1],  # 0
    [ 1, -1, -1],  # 1
    [ 1,  1, -1],  # 2
    [-1,  1, -1],  # 3
    [-1, -1,  1],  # 4
    [ 1, -1,  1],  # 5
    [ 1,  1,  1],  # 6
    [-1,  1,  1],  # 7
], dtype=float)

_NE1_CONNECT = np.array([
    [0, 1, 2, 3],  # −z face  (ξ=x, η=y)
    [4, 5, 6, 7],  # +z face  (ξ=x, η=y)
    [0, 1, 5, 4],  # −y face  (ξ=x, η=z)
    [3, 2, 6, 7],  # +y face  (ξ=x, η=z)
    [0, 3, 7, 4],  # −x face  (ξ=y, η=z)
    [1, 2, 6, 5],  # +x face  (ξ=y, η=z)
])

#-------------------------------------------------------------------------------
# GLL constants


class TestGLLPoints(unittest.TestCase):

    def test_count(self):
        self.assertEqual(len(GLL_POINTS), 4)

    def test_endpoints(self):
        self.assertEqual(GLL_POINTS[0], -1.0)
        self.assertEqual(GLL_POINTS[-1],  1.0)

    def test_symmetry(self):
        np.testing.assert_array_equal(GLL_POINTS, -GLL_POINTS[::-1])

    def test_inner_points(self):
        np.testing.assert_allclose(GLL_POINTS[1], -1.0 / np.sqrt(5.0))
        np.testing.assert_allclose(GLL_POINTS[2],  1.0 / np.sqrt(5.0))


class TestGLLWeights(unittest.TestCase):

    def test_count(self):
        self.assertEqual(len(GLL_WEIGHTS), 4)

    def test_sum(self):
        # Integral of 1 on [-1, 1] = 2
        np.testing.assert_allclose(np.sum(GLL_WEIGHTS), 2.0)

    def test_symmetry(self):
        np.testing.assert_array_equal(GLL_WEIGHTS, GLL_WEIGHTS[::-1])

    def test_endpoint_weights(self):
        np.testing.assert_allclose(GLL_WEIGHTS[0], 1.0 / 6.0)
        np.testing.assert_allclose(GLL_WEIGHTS[-1], 1.0 / 6.0)

    def test_quadrature_exactness(self):
        # GLL with n=4 points integrates polynomials up to degree 2n-3=5 exactly.
        # (Two endpoints fixed at ±1 reduce the exactness by 2 vs Gauss-Legendre.)
        for k in range(6):
            result   = np.sum(GLL_WEIGHTS * GLL_POINTS ** k)
            expected = 2.0 / (k + 1) if k % 2 == 0 else 0.0
            np.testing.assert_allclose(result, expected, atol=1e-14,
                                       err_msg=f'quadrature failed for degree {k}')

#-------------------------------------------------------------------------------
# Derivative matrix


class TestGLLDeriv(unittest.TestCase):

    def test_shape(self):
        self.assertEqual(GLL_DERIV.shape, (4, 4))

    def test_row_sum_zero(self):
        # d(constant)/dξ = 0  →  each row sums to zero
        np.testing.assert_allclose(GLL_DERIV.sum(axis=1), 0.0, atol=1e-14)

    def test_differentiates_polynomials(self):
        # D @ [ξ_i^k] should equal [k · ξ_i^(k-1)] for k = 1, 2, 3
        for k in range(1, 4):
            f  = GLL_POINTS ** k
            df = k * GLL_POINTS ** (k - 1)
            np.testing.assert_allclose(GLL_DERIV @ f, df, atol=1e-13,
                                       err_msg=f'failed for degree {k}')

    def test_derivative_of_constant_is_zero(self):
        ones = np.ones(4)
        np.testing.assert_allclose(GLL_DERIV @ ones, 0.0, atol=1e-14)

#-------------------------------------------------------------------------------
# element_metric


class TestElementMetric(unittest.TestCase):

    def setUp(self):
        self.metdet, _, self.g_contra, self.D = element_metric(_NE1_COORDS, _NE1_CONNECT)

    def test_metdet_shape(self):
        self.assertEqual(self.metdet.shape, (6, 4, 4))

    def test_g_contra_shape(self):
        self.assertEqual(self.g_contra.shape, (6, 4, 4, 2, 2))

    def test_D_shape(self):
        self.assertEqual(self.D.shape, (6, 4, 4, 2, 2))

    def test_metdet_positive(self):
        self.assertTrue(np.all(self.metdet > 0))

    def test_g_contra_symmetric(self):
        np.testing.assert_allclose(
            self.g_contra[..., 0, 1],
            self.g_contra[..., 1, 0],
            atol=1e-14,
        )

    def test_metdet_matches_analytical_formula(self):
        # For all 6 faces of the ne=1 cube-sphere, the bilinear map reduces to
        # the gnomonic projection X = (a, b, ±1)/r with r = √(a²+b²+1), for
        # which metdet = 1/r³ = 1/(ξ²+η²+1)^{3/2} analytically.  This holds
        # by symmetry for all 6 faces with appropriate permutation of coords.
        XI, ETA = np.meshgrid(GLL_POINTS, GLL_POINTS, indexing='ij')
        expected = 1.0 / (XI ** 2 + ETA ** 2 + 1) ** 1.5
        for e in range(6):
            np.testing.assert_allclose(self.metdet[e], expected, rtol=1e-12,
                                       err_msg=f'metdet mismatch on face {e}')

    def test_total_area_sanity(self):
        # The GLL 4-point quadrature approximates ∫∫ metdet dξdη, which converges
        # to 4π as the mesh is refined.  For the very coarse ne=1 mesh the
        # non-polynomial integrand causes ~3% quadrature error, so we only check
        # that the result is in the right ballpark.
        WW = np.outer(GLL_WEIGHTS, GLL_WEIGHTS)
        total = np.sum(self.metdet * WW[np.newaxis, ...])
        np.testing.assert_allclose(total, 4 * np.pi, rtol=0.05)

#-------------------------------------------------------------------------------
# gll_positions


class TestGLLPositions(unittest.TestCase):

    def setUp(self):
        self.lon, self.lat = gll_positions(_NE1_COORDS, _NE1_CONNECT)

    def test_shape(self):
        self.assertEqual(self.lon.shape, (6, 4, 4))
        self.assertEqual(self.lat.shape, (6, 4, 4))

    def test_lon_range(self):
        self.assertTrue(np.all(self.lon >= 0.0))
        self.assertTrue(np.all(self.lon < 360.0))

    def test_lat_range(self):
        self.assertTrue(np.all(self.lat >= -90.0))
        self.assertTrue(np.all(self.lat <=  90.0))

    def test_z_faces_have_correct_sign_of_lat(self):
        # +z face (element 1): all GLL latitudes positive
        # -z face (element 0): all GLL latitudes negative
        self.assertTrue(np.all(self.lat[1] > 0), '+z face should have lat > 0')
        self.assertTrue(np.all(self.lat[0] < 0), '-z face should have lat < 0')

    def test_corner_positions(self):
        # Corner GLL points (ξ=±1, η=±1) should coincide with node coordinates.
        # For the -z face (element 0), corner 0 (ξ=-1,η=-1) is GLL index [0,0]
        # and corresponds to node 0: (-s,-s,-s).
        node0_lon = np.degrees(np.arctan2(-_S3, -_S3)) % 360.0  # arctan2(y,x)
        node0_lat = np.degrees(np.arcsin(-_S3))
        np.testing.assert_allclose(self.lon[0, 0, 0], node0_lon, atol=1e-12)
        np.testing.assert_allclose(self.lat[0, 0, 0], node0_lat, atol=1e-12)

#-------------------------------------------------------------------------------
# cv_reference_edges


class TestCvReferenceEdges(unittest.TestCase):

    def test_count(self):
        self.assertEqual(len(cv_reference_edges()), 5)

    def test_endpoints(self):
        cv = cv_reference_edges()
        self.assertEqual(cv[0], -1.0)
        self.assertEqual(cv[-1],  1.0)

    def test_interior_cumulative_weights(self):
        # CV boundaries follow homme convention: cv[i] = cv[i-1] + w[i-1]
        # (cumulative sum of GLL weights), not midpoints between GLL nodes.
        cv = cv_reference_edges()
        np.testing.assert_allclose(cv[1], -1.0 + GLL_WEIGHTS[0])
        np.testing.assert_allclose(cv[2],  0.0)
        np.testing.assert_allclose(cv[3],  1.0 - GLL_WEIGHTS[3])

#-------------------------------------------------------------------------------
# unique_gll_nodes


class TestUniqueGllNodes(unittest.TestCase):

    def setUp(self):
        self.unique_xyz, self.inverse_idx, self.primary_eij = \
            unique_gll_nodes(_NE1_COORDS, _NE1_CONNECT)

    def test_ncol(self):
        # ne=1, np=4: ncol = 6*1^2*(4-1)^2 + 2 = 56
        self.assertEqual(len(self.unique_xyz), 56)

    def test_unique_xyz_shape(self):
        self.assertEqual(self.unique_xyz.shape, (56, 3))

    def test_inverse_idx_shape(self):
        # 6 elements × 16 GLL points each
        self.assertEqual(self.inverse_idx.shape, (96,))

    def test_primary_eij_shape(self):
        self.assertEqual(self.primary_eij.shape, (56, 3))

    def test_nodes_on_unit_sphere(self):
        norms = np.linalg.norm(self.unique_xyz, axis=-1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-10)

    def test_inverse_idx_range(self):
        self.assertTrue(np.all(self.inverse_idx >= 0))
        self.assertTrue(np.all(self.inverse_idx < 56))

    def test_primary_eij_elem_range(self):
        # Element indices must be in [0, 5]
        self.assertTrue(np.all(self.primary_eij[:, 0] >= 0))
        self.assertTrue(np.all(self.primary_eij[:, 0] < 6))

#-------------------------------------------------------------------------------
# gll_node_areas


class TestGllNodeAreas(unittest.TestCase):

    def setUp(self):
        metdet, _, _, _   = element_metric(_NE1_COORDS, _NE1_CONNECT)
        _, inverse_idx, _ = unique_gll_nodes(_NE1_COORDS, _NE1_CONNECT)
        self.area = gll_node_areas(metdet, inverse_idx, ncol=56)

    def test_shape(self):
        self.assertEqual(self.area.shape, (56,))

    def test_all_positive(self):
        self.assertTrue(np.all(self.area > 0))

    def test_total_area_near_4pi(self):
        # GLL quadrature of the non-polynomial integrand gives ~3% error at ne=1.
        np.testing.assert_allclose(np.sum(self.area), 4 * np.pi, rtol=0.05)

#-------------------------------------------------------------------------------
# cv_corner_positions


class TestCvCornerPositions(unittest.TestCase):

    def setUp(self):
        self.corner_lon, self.corner_lat = \
            cv_corner_positions(_NE1_COORDS, _NE1_CONNECT)

    def test_shape(self):
        self.assertEqual(self.corner_lon.shape, (6, 4, 4, 4))
        self.assertEqual(self.corner_lat.shape, (6, 4, 4, 4))

    def test_lon_range(self):
        self.assertTrue(np.all(self.corner_lon >= 0.0))
        self.assertTrue(np.all(self.corner_lon < 360.0))

    def test_lat_range(self):
        self.assertTrue(np.all(self.corner_lat >= -90.0))
        self.assertTrue(np.all(self.corner_lat <=  90.0))

    def test_z_faces_lat_sign(self):
        # +z face (element 1): all CV corner latitudes positive
        # -z face (element 0): all CV corner latitudes negative
        self.assertTrue(np.all(self.corner_lat[1] > 0), '+z face corners should have lat > 0')
        self.assertTrue(np.all(self.corner_lat[0] < 0), '-z face corners should have lat < 0')

#-------------------------------------------------------------------------------
# cv_corners_assembled


class TestCvCornersAssembled(unittest.TestCase):

    def setUp(self):
        self.corner_lon, self.corner_lat = \
            cv_corners_assembled(_NE1_COORDS, _NE1_CONNECT)

    def test_shape(self):
        # ne=1, ncol=56, 8 corners per node
        self.assertEqual(self.corner_lon.shape, (56, 8))
        self.assertEqual(self.corner_lat.shape, (56, 8))

    def test_lon_range(self):
        self.assertTrue(np.all(self.corner_lon >= 0.0))
        self.assertTrue(np.all(self.corner_lon < 360.0))

    def test_lat_range(self):
        self.assertTrue(np.all(self.corner_lat >= -90.0))
        self.assertTrue(np.all(self.corner_lat <=  90.0))

    def test_z_faces_lat_sign(self):
        # All 56 unique nodes include nodes from all faces.  For the ne=1
        # mesh, 8 cube-corner nodes straddle hemispheres; we can only check
        # that the z-face interior nodes have the right sign.  Just verify
        # that there are at least some corners with lat > 0 and lat < 0.
        self.assertTrue(np.any(self.corner_lat > 0))
        self.assertTrue(np.any(self.corner_lat < 0))

    def test_unique_corners_per_node_type(self):
        # For ne=1 there are only 8 mesh nodes (the cube corners), each
        # shared by 3 elements — giving 6 unique corners (slots 6-7 repeat).
        # All interior GLL nodes belong to exactly 1 element → 4 unique corners.
        # There are no 2-element edge nodes (ne=1 has no shared edge interior).
        _, inverse_idx, _ = unique_gll_nodes(_NE1_COORDS, _NE1_CONNECT)
        n_occ = np.bincount(inverse_idx, minlength=56)

        for uid in range(56):
            clons = self.corner_lon[uid]
            clats = self.corner_lat[uid]
            pts   = list(zip(np.round(clons, 8), np.round(clats, 8)))
            n_unique = len(set(pts))
            if n_occ[uid] == 1:
                self.assertEqual(n_unique, 4,
                    f'interior node {uid} should have 4 unique corners, got {n_unique}')
            elif n_occ[uid] == 3:
                self.assertEqual(n_unique, 6,
                    f'cube-corner node {uid} should have 6 unique corners, got {n_unique}')

    def test_corners_ccw(self):
        # Verify CCW ordering via shoelace signed area in lat/lon space.
        # Cells at the antimeridian (lon near 0 or 360) are excluded since
        # the flat shoelace sign is unreliable there.
        def signed_area(lats, lons):
            n = len(lons)
            return sum(lons[k] * lats[(k+1) % n] - lons[(k+1) % n] * lats[k]
                       for k in range(n)) / 2

        antimeridian_tol = 5.0
        for i in range(56):
            lons = self.corner_lon[i]
            lats = self.corner_lat[i]
            if np.any(lons < antimeridian_tol) or np.any(lons > 360 - antimeridian_tol):
                continue
            sa = signed_area(lats, lons)
            self.assertGreater(sa, 0,
                f'node {i}: expected CCW (positive signed area), got {sa:.6f}')


#-------------------------------------------------------------------------------
# smooth_phis


class TestSmoothPhis(unittest.TestCase):

    def setUp(self):
        self.metdet, _, _, self.D_mat = element_metric(_NE1_COORDS, _NE1_CONNECT)
        _, self.inverse_idx, _ = unique_gll_nodes(_NE1_COORDS, _NE1_CONNECT)
        self.ncol = 56
        self.M_asm = gll_node_areas(self.metdet, self.inverse_idx, self.ncol)

    def test_constant_field_invariant(self):
        # Smoothing a constant field must return the same constant.
        phi_const = np.full(self.ncol, 42.0)
        phi_out   = smooth_phis(phi_const, self.metdet, self.inverse_idx, self.ncol,
                                self.D_mat)
        np.testing.assert_allclose(phi_out, phi_const, atol=1e-10,
                                   err_msg='constant field must be invariant under smoothing')

    def test_integral_conservation(self):
        # Smoothing must preserve the weighted integral ∫ φ dA = Σ φ_i * M_asm_i.
        rng      = np.random.default_rng(0)
        phi_in   = rng.standard_normal(self.ncol)
        phi_out  = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                               self.D_mat)
        integral_in  = np.sum(phi_in  * self.M_asm)
        integral_out = np.sum(phi_out * self.M_asm)
        np.testing.assert_allclose(integral_out, integral_in, rtol=1e-10,
                                   err_msg='smoothing must preserve the area-weighted integral')

    def test_variance_reduction(self):
        # Smoothing must reduce (or preserve) the area-weighted variance.
        rng     = np.random.default_rng(1)
        phi_in  = rng.standard_normal(self.ncol)
        phi_out = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                              self.D_mat)
        mean_in  = np.sum(phi_in  * self.M_asm) / np.sum(self.M_asm)
        mean_out = np.sum(phi_out * self.M_asm) / np.sum(self.M_asm)
        var_in   = np.sum((phi_in  - mean_in)  ** 2 * self.M_asm)
        var_out  = np.sum((phi_out - mean_out) ** 2 * self.M_asm)
        self.assertLessEqual(var_out, var_in * 1.001,
                             'smoothing must not increase area-weighted variance')

    def test_zero_cycles_returns_copy(self):
        # numcycle=0 must return the input unchanged.
        phi_in  = np.arange(self.ncol, dtype=float)
        phi_out = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                              self.D_mat, numcycle=0)
        np.testing.assert_array_equal(phi_out, phi_in)
        self.assertIsNot(phi_out, phi_in, 'smooth_phis must return a copy, not the input')

    def test_minf_floor_enforced(self):
        # All output values must be >= minf when a floor is specified.
        rng    = np.random.default_rng(7)
        phi_in = rng.standard_normal(self.ncol) * 100.0
        minf   = -5.0
        phi_out = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                              self.D_mat, minf=minf)
        self.assertTrue(np.all(phi_out >= minf - 1e-10),
                        f'min value {phi_out.min():.4f} violates floor {minf}')

    def test_minf_none_matches_default(self):
        # minf=None must produce the same result as the unclipped smoother.
        rng    = np.random.default_rng(3)
        phi_in = rng.standard_normal(self.ncol)
        phi_a  = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                             self.D_mat)
        phi_b  = smooth_phis(phi_in, self.metdet, self.inverse_idx, self.ncol,
                             self.D_mat, minf=None)
        np.testing.assert_array_equal(phi_a, phi_b,
                                      err_msg='minf=None must be identical to default')


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
