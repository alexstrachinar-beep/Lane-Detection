from collections import deque
import cv2
import numpy as np

cam = cv2.VideoCapture('Lane Detection Test Video 01.mp4')

THRESHOLD = 190
MIN_POINTS = 10

# Historic pentru netezirea mișcării (Moving Average)
left_top_history = deque(maxlen=4)
left_bot_history = deque(maxlen=4)
right_top_history = deque(maxlen=4)
right_bot_history = deque(maxlen=4)

# Valori de rezervă
left_top_roi = (0, 0)
left_bottom = (0, 0)
right_top_roi = (0, 0)
right_bottom = (0, 0)

while True:
    ret, frame = cam.read()
    if not ret:
        break

    # Task 2 - Resize
    frame = cv2.resize(frame, (320, 180))
    height, width = frame.shape[:2]

    # Task 3 - Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Task 4 - Trapezoid
    mask = np.zeros((height, width), dtype=np.uint8)

    pt1 = (int(width * 0.58), int(height * 0.60))
    pt2 = (int(width * 0.42), int(height * 0.60))
    pt3 = (int(width * 0.20), height)
    pt4 = (int(width * 0.80), height)

    trapezoid_points = np.array([pt1, pt2, pt3, pt4], dtype=np.int32)
    cv2.fillConvexPoly(mask, trapezoid_points, 1)
    road = gray * mask

    # Task 5 - Top-Down View
    frame_bounds = np.float32(
        [[width, 0], [0, 0], [0, height], [width, height]]
    )
    trapezoid_bounds = np.float32(trapezoid_points)

    magic_matrix = cv2.getPerspectiveTransform(
        trapezoid_bounds, frame_bounds
    )
    top_view = cv2.warpPerspective(road, magic_matrix, (width, height))

    # Task 6 - Blur
    blurred = cv2.blur(top_view, ksize=(5, 5))

    # Task 7 - Sobel Edge Detection
    sobel_v = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    sobel_h = np.transpose(sobel_v)

    blurred_f = np.float32(blurred)
    v_edges = cv2.filter2D(blurred_f, -1, sobel_v)
    h_edges = cv2.filter2D(blurred_f, -1, sobel_h)

    edges = cv2.convertScaleAbs(np.sqrt(v_edges**2 + h_edges**2))

    # Task 8 - Binarizare
    _, binary = cv2.threshold(edges, THRESHOLD, 255, cv2.THRESH_BINARY)

    # Task 9 - Extragere coordonate din ROI
    binary_clean = binary.copy()
    margin = int(width * 0.05)
    binary_clean[:, :margin] = 0
    binary_clean[:, width - margin :] = 0

    roi_y = int(height * 0.65)

    left_half = binary_clean[:, : width // 2]
    right_half = binary_clean[:, width // 2 :]

    left_pts = np.argwhere(left_half[roi_y:, :] == 255)
    right_pts = np.argwhere(right_half[roi_y:, :] == 255)

    if len(left_pts) > 0:
        left_pts[:, 0] += roi_y
    if len(right_pts) > 0:
        right_pts[:, 0] += roi_y

    left_ys = left_pts[:, 0] if len(left_pts) > 0 else np.array([])
    left_xs = left_pts[:, 1] if len(left_pts) > 0 else np.array([])

    right_ys = right_pts[:, 0] if len(right_pts) > 0 else np.array([])
    right_xs = (
        (right_pts[:, 1] + width // 2) if len(right_pts) > 0 else np.array([])
    )

    # Task 10 - Regresie Liniară (Verificăm să avem suficiente puncte distanțate pe Y)
    if len(left_xs) > MIN_POINTS and len(np.unique(left_ys)) >= 3:
        poly_left = np.polynomial.polynomial.polyfit(left_ys, left_xs, deg=1)
        b_left, a_left = poly_left[0], poly_left[1]

        x_bot = int(a_left * height + b_left)
        x_top = int(a_left * roi_y + b_left)

        if -10**5 < x_bot < 10**5:
            left_bot_history.append((x_bot, height))
            left_top_history.append((x_top, roi_y))

    if len(right_xs) > MIN_POINTS and len(np.unique(right_ys)) >= 3:
        poly_right = np.polynomial.polynomial.polyfit(
            right_ys, right_xs, deg=1
        )
        b_right, a_right = poly_right[0], poly_right[1]

        x_bot = int(a_right * height + b_right)
        x_top = int(a_right * roi_y + b_right)

        if -10**5 < x_bot < 10**5:
            right_bot_history.append((x_bot, height))
            right_top_history.append((x_top, roi_y))

    # Mediere temporală
    if left_bot_history:
        left_bottom = (int(np.mean([p[0] for p in left_bot_history])), height)
        left_top_roi = (int(np.mean([p[0] for p in left_top_history])), roi_y)

    if right_bot_history:
        right_bottom = (
            int(np.mean([p[0] for p in right_bot_history])),
            height,
        )
        right_top_roi = (
            int(np.mean([p[0] for p in right_top_history])),
            roi_y,
        )

    # Task 11 - Proiecția înapoi
    left_line_frame = np.zeros((height, width), dtype=np.uint8)
    right_line_frame = np.zeros((height, width), dtype=np.uint8)

    cv2.line(left_line_frame, left_top_roi, left_bottom, 255, 4)
    cv2.line(right_line_frame, right_top_roi, right_bottom, 255, 4)

    inverse_matrix = cv2.getPerspectiveTransform(
        frame_bounds, trapezoid_bounds
    )

    left_line_warped = cv2.warpPerspective(
        left_line_frame, inverse_matrix, (width, height)
    )
    right_line_warped = cv2.warpPerspective(
        right_line_frame, inverse_matrix, (width, height)
    )

    left_coords = np.argwhere(left_line_warped == 255)
    right_coords = np.argwhere(right_line_warped == 255)

    final_frame = frame.copy()

    # Colorare
    final_frame[left_coords[:, 0], left_coords[:, 1]] = (50, 50, 250)
    final_frame[right_coords[:, 0], right_coords[:, 1]] = (50, 250, 50)

    cv2.imshow("Final Lane Detection", final_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()