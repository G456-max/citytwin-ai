import numpy as np

class GCPAnchorEngine:
    """Computes coordinate transformation matrices using Ground Control Point (GCP) snapping."""

    @staticmethod
    def calculate_affine_transform(
        source_gcp: list[tuple[float, float]], 
        target_gcp: list[tuple[float, float]]
    ) -> np.ndarray:
        """
        Calculates the 3x3 affine transformation matrix mapping source coords to targets.
        
        Args:
            source_gcp: 3 anchor points in local CAD coordinate systems.
            target_gcp: 3 matching anchor points in real-world WGS84 GPS coordinate systems.

        Returns:
            A 3x3 numpy array containing the affine conversion matrix.
        """
        if len(source_gcp) < 3 or len(target_gcp) < 3:
            raise ValueError("3 Ground Control Points (GCPs) are required for affine snapping.")

        # Construct coordinate system linear equations (A * X = B)
        # For each point: target_x = a*source_x + b*source_y + c
        #                 target_y = d*source_x + e*source_y + f
        A = []
        B_x = []
        B_y = []
        
        for i in range(3):
            src_x, src_y = source_gcp[i]
            tgt_x, tgt_y = target_gcp[i]
            A.append([src_x, src_y, 1.0])
            B_x.append(tgt_x)
            B_y.append(tgt_y)

        # Solve equations using least-squares numpy solver
        coef_x, _, _, _ = np.linalg.lstsq(A, B_x, rcond=None)
        coef_y, _, _, _ = np.linalg.lstsq(A, B_y, rcond=None)

        # Build 3x3 transformation matrix
        transform_matrix = np.array([
            [coef_x[0], coef_x[1], coef_x[2]],
            [coef_y[0], coef_y[1], coef_y[2]],
            [0.0, 0.0, 1.0]
        ])
        
        return transform_matrix

    @staticmethod
    def transform_points(points: list[tuple[float, float]], transform_matrix: np.ndarray) -> list[tuple[float, float]]:
        """Applies the calculated affine matrix transformation to a list of coordinates."""
        transformed = []
        for x, y in points:
            vec = np.array([x, y, 1.0])
            res = np.dot(transform_matrix, vec)
            transformed.append((res[0], res[1]))
        return transformed
