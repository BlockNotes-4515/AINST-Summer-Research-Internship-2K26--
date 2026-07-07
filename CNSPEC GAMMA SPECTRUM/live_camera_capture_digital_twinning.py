from MCALib import MCA
import cv2
import numpy as np
import time
import threading


# =========================
# MCA CONNECTION
# =========================

m = MCA(port="COM11")

if not m.connected:
    print("MCA failed")
    exit()

print("MCA Connected")

m.clearHistogram()
m.startHistogram()



# =========================
# GLOBAL VALUES
# =========================

radiation_level = 0
counts = 0



# =========================
# GAMMA MONITOR
# =========================

def gamma_reading():

    global radiation_level
    global counts


    while True:

        time.sleep(1)

        m.sync()

        spectrum=np.array(
            m.getHistogram()
        )


        counts=int(
            spectrum.sum()
        )


        # intensity mapping

        if counts < 200:

            radiation_level=0.1


        elif counts < 600:

            radiation_level=0.5


        elif counts < 1000:

            radiation_level=0.8


        else:

            radiation_level=1.0



        print(
            "Counts:",
            counts,
            "Intensity:",
            radiation_level
        )





# =========================
# CAMERA DIGITAL TWIN
# =========================


def camera():

    cam=cv2.VideoCapture(0)



    while True:


        ret,frame=cam.read()

        if not ret:
            break



        frame=cv2.resize(
            frame,
            (640,480)
        )



        # Digital twin depth style

        gray=cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )


        depth=cv2.applyColorMap(
            gray,
            cv2.COLORMAP_JET
        )



        # -----------------------
        # Radiation heat zone
        # -----------------------


        heat=np.zeros_like(frame)



        # assumed source position
        # center of camera

        x=320
        y=240



        radius=int(
            40+
            radiation_level*180
        )



        cv2.circle(

            heat,

            (x,y),

            radius,

            (
                0,
                0,
                255
            ),

            -1

        )



        # intensity color


        if radiation_level <0.3:

            color=(255,0,0)


        elif radiation_level <0.7:

            color=(0,255,255)


        elif radiation_level <0.9:

            color=(0,165,255)


        else:

            color=(0,0,255)



        heat[:]=0


        cv2.circle(

            heat,

            (x,y),

            radius,

            color,

            -1

        )



        # blend radiation with digital twin


        output=cv2.addWeighted(

            depth,

            0.8,

            heat,

            0.35,

            0

        )



        cv2.putText(

            output,

            f"Gamma Counts: {counts}",

            (20,40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255,255,255),

            2

        )


        cv2.imshow(

            "Radiation Digital Twin",

            output

        )



        if cv2.waitKey(1)==ord('q'):

            break



    cam.release()
    cv2.destroyAllWindows()




# =========================
# START
# =========================


threading.Thread(

    target=gamma_reading,

    daemon=True

).start()



camera()