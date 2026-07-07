import cv2
import numpy as np


# Camera
cap = cv2.VideoCapture(0)


if not cap.isOpened():
    print("Camera not detected")
    exit()



while True:


    ret, frame = cap.read()


    if not ret:
        break



    # Resize
    frame = cv2.resize(
        frame,
        (640,480)
    )



    # Convert grayscale

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )



    # Create artificial depth map

    depth = cv2.applyColorMap(
        gray,
        cv2.COLORMAP_JET
    )



    # Edge detection

    edges = cv2.Canny(
        gray,
        80,
        150
    )


    edges = cv2.cvtColor(
        edges,
        cv2.COLOR_GRAY2BGR
    )



    # Digital twin fusion

    digital_twin = cv2.addWeighted(
        depth,
        0.7,
        edges,
        0.3,
        0
    )



    # Add grid effect

    for x in range(0,640,40):

        cv2.line(
            digital_twin,
            (x,0),
            (x,480),
            (255,255,255),
            1
        )


    for y in range(0,480,40):

        cv2.line(
            digital_twin,
            (0,y),
            (640,y),
            (255,255,255),
            1
        )



    cv2.putText(

        digital_twin,

        "3D DIGITAL TWIN MODE",

        (20,40),

        cv2.FONT_HERSHEY_SIMPLEX,

        1,

        (255,255,255),

        2

    )



    cv2.imshow(
        "Live 3D Digital Twin Camera",
        digital_twin
    )



    if cv2.waitKey(1)==ord('q'):
        break



cap.release()
cv2.destroyAllWindows()