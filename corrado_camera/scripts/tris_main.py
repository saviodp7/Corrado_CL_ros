#!/usr/bin/env python3
import rospy

import cv2
import os
import time

from grid import find_game_grid, print_board, find_color
from setting import X_SYM, O_SYM
from MinMaxSolver import MinMaxSolver
from LetterRecognition import LetterRecognition

def main():
    rospy.init_node("corrado_camera_node", anonymous=True)

    # Inizializza la webcam
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("config", cv2.WINDOW_NORMAL)
    cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("threshold", "mask", 77, 255, lambda x: None)
    cv2.createTrackbar("kernel_dim", "mask", 10, 15, lambda x: None)

    # Crea un'istanza della classe con il percorso dei pesi del modello
    current_path = os.path.dirname(__file__)
    relative_path = 'weights.best.xo.hdf5'
    full_path = os.path.join(current_path, relative_path)
    letter_recog = LetterRecognition(full_path)

    # Gestione campionamento
    rate = rospy.Rate(2) # 2Hz
    accuracy_count = 0
    prec_config = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    solver = MinMaxSolver()

    while not rospy.is_shutdown():

        config = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        ret, frame = cap.read()
        threshold = cv2.getTrackbarPos("threshold", "mask")
        kernel_dim = cv2.getTrackbarPos("kernel_dim", "mask")

        try:
            # Trova e disegna la griglia del tris
            grid_frame, thresholded, corners = find_game_grid(frame, threshold, kernel_dim)

            for index, cell in enumerate(corners):
                extracted_frame = grid_frame[cell[0][1]:cell[1][1], cell[0][0]:cell[1][0]]
                (h, w) = extracted_frame.shape[:2]
                cv2.imwrite("frame_estratto.jpg", extracted_frame)
                if find_color(extracted_frame):
                    # Utilizza la classe per riconoscere le lettere
                    recognized_letter = letter_recog.recognize_letter("frame_estratto.jpg")
                    if recognized_letter == 'х':
                        config[index] = X_SYM
                        cv2.line(extracted_frame, (10, 10), (h-10, h-10), (0, 0, 255), 2)
                        cv2.line(extracted_frame, (10, h-10), (h-10, 10), (0, 0, 255), 2)
                    elif recognized_letter == 'о':
                        config[index] = O_SYM
                        cv2.circle(extracted_frame, (w//2, h//2), 22, (0, 0, 255), 2)
                else:
                    config[index] = 0
        except TypeError:
            pass

        # Mostra il frame elaborato
        cv2.imshow("config", frame) #grid_frame
        # DEBUG
        cv2.imshow("mask", thresholded)

        # Assicuriamoci dell'accuratezza della rilevazione
        if config == prec_config:
            accuracy_count += 1
        else:
            accuracy_count = 0
        prec_config = config

        # Stampo la mossa migliore
        if accuracy_count > 10:
            print_board(config)
            solver.set_config(config)
            print("La mossa ottima è: ", solver.find_best_move())


        if cv2.waitKey(1) & 0xFF == 27:  # Esc per uscire
            break

        rate.sleep()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass