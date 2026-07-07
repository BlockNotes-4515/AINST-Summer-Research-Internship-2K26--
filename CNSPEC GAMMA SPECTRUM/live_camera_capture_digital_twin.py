from MCALib import MCA
import cv2
import numpy as np
import threading
import time



# ==============================
# MCA CONNECTION
# ==============================

m = MCA(port="COM11")


if not m.connected:
    print("MCA connection failed")
    exit()


print("Gamma Detector Connected")


m.clearHistogram()
m.startHistogram()



# ==============================
# GLOBAL VALUES
# ==============================


radiation_intensity = 0

radiation_color = (
    255,
    0,
    0
)


counts_value = 0



# ==============================
# RADIATION ANALYSIS
# ==============================


def analyze_radiation(counts):

    global radiation_color


    if counts < 200:


        radiation_color = (
            255,
            0,
            0
        )
        # Blue


        return 0.2



    elif counts < 600:


        radiation_color = (
            0,
            255,
            255
        )
        # Yellow


        return 0.6



    elif counts < 1000:


        radiation_color = (
            0,
            165,
            255
        )
        # Orange


        return 0.8



    else:


        radiation_color = (
            0,
            0,
            255
        )
        # Red


        return 1.0





# ==============================
# GAMMA THREAD
# ==============================


def gamma_monitor():

    global radiation_intensity
    global counts_value


    while True:


        time.sleep(1)


        m.sync()


        spectrum=np.array(
            m.getHistogram()
        )


        counts_value=int(
            spectrum.sum()
        )


        peak=int(
            spectrum.argmax()
        )


        radiation_intensity = analyze_radiation(
            counts_value
        )


        print(
            "Counts:",
            counts_value,
            "Peak:",
            peak,
            "Intensity:",
            radiation_intensity
        )






# ==============================
# CAMERA DIGITAL TWIN
# ==============================


def camera_monitor():


    cam=cv2.VideoCapture(0)



    while True:


        ret,frame=cam.read()


        if not ret:
            break



        frame=cv2.resize(
            frame,
            (640,480)
        )



        # Depth style

        gray=cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )


        depth=cv2.applyColorMap(
            gray,
            cv2.COLORMAP_JET
        )



        edges=cv2.Canny(
            gray,
            80,
            150
        )


        edges=cv2.cvtColor(
            edges,
            cv2.COLOR_GRAY2BGR
        )



        digital_twin=cv2.addWeighted(
            depth,
            0.7,
            edges,
            0.3,
            0
        )




        # ======================
        # RADIATION SOURCE EFFECT
        # ======================



        radius=int(
            50 +
            radiation_intensity*150
        )


        overlay=digital_twin.copy()



        cv2.circle(

            overlay,

            (
                320,
                240
            ),

            radius,

            radiation_color,

            -1

        )



        digital_twin=cv2.addWeighted(

            overlay,

            0.35,

            digital_twin,

            0.65,

            0

        )



        # Information panel


        cv2.putText(

            digital_twin,

            "Radiation Counts : "
            +str(counts_value),

            (20,40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255,255,255),

            2

        )


        cv2.putText(

            digital_twin,

            "3D Radiation Digital Twin",

            (20,80),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255,255,255),

            2

        )




        cv2.imshow(

            "Radiation Digital Twin",

            digital_twin

        )



        if cv2.waitKey(1)==ord('q'):

            break




    cam.release()

    cv2.destroyAllWindows()





# ==============================
# START SYSTEM
# ==============================


threading.Thread(

    target=gamma_monitor,

    daemon=True

).start()



camera_monitor()

