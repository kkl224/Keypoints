import cv2
import math
import time
import numpy as np

MAX_FRAMES = 600  # large numbers will cover the whole video
INTERVAL = 100 # 150 frames per inverval

# Create an ORB object and detect keypoints and descriptors in the template
orb = cv2.ORB_create()
# Create a brute-force matcher object
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def extract_keypoints(video):
    # Create a VideoCapture object to read the video file
    cap = cv2.VideoCapture(video)
    # Extract all keypoints and descriptors by frame
    frame_kpt, frame_des = [], []
    video_frames = []
    k = 0
    # Loop through the video frames
    while cap.isOpened() and k < MAX_FRAMES + 1:
        # Read a frame from the video
        ret, frame = cap.read()
        # Check if the frame was successfully read
        if not ret: continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kpt, des = orb.detectAndCompute(gray, None)
        if des is None:
            print("No keypoints/descriptors in frame ", k)
            continue
        print("Frame", k)
        frame_kpt.append(kpt)
        frame_des.append(des)
        video_frames.append(frame)
        # frame = cv2.drawKeypoints(frame, kpt, None, color=(0, 255, 0), flags=0)
        # cv2.imshow("frame", frame)
        k += 1
        # Wait for Esc key to stop
        if cv2.waitKey(1) == 27:
            # De-allocate any associated memory usage
            cv2.destroyAllWindows()
            cap.release()
            break
    cap.release()
    return frame_kpt, frame_des, video_frames


def save_kpt_des(keypoints, descriptors, filename):
    fs = cv2.FileStorage(filename, cv2.FILE_STORAGE_WRITE)
    # Write the descriptors to the file
    fs.write("descriptors", descriptors)
    # Convert keypoints to a numpy array
    keypoints_array = np.array([keypoint.pt for keypoint in keypoints])
    # Write the keypoints to the file
    fs.write("keypoints", keypoints_array)  
    fs.release()


def analyze_kpt_des(frame, keypoints, descriptors, filename, video):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 10
    out = cv2.VideoWriter(video, fourcc, fps, (400, 300))
    kpts_cur, des_cur = [], []
    kpts_fin, des_fin = [], []
    k = INTERVAL
    while k > 0:
        k -= 1
        if k == INTERVAL - 1:
            kpts_cur = keypoints[k] #current frame keypoints
            des_cur = descriptors[k] #current frame descriptors
            kpts_fin = keypoints[k] #reference frame keypoints
            des_fin = descriptors[k] #reference frame descriptors
            continue
        else:
            kpts_cur = keypoints[k] #current frame keypoints
            des_cur = descriptors[k] #current frame descriptors
        if descriptors is None:
            print("No keypoints/descriptors in frame")
            continue
        matches = bf.match(des_fin, descriptors[k])
        matches = sorted(matches, key=lambda x: x.distance)
        # matches = [m for m in matches if m.distance < MAX_MATCH_DISTANCE]
        kpts_cur_temp = []
        des_cur_temp = []
        kpts_fin_temp = []
        des_fin_temp = []
        for match in matches:
            query_idx = match.queryIdx
            kpts_fin_temp.append(kpts_fin[query_idx])
            des_fin_temp.append(des_fin[query_idx])
            train_idx = match.trainIdx
            kpts_cur_temp.append(kpts_cur[train_idx])
            des_cur_temp.append(des_cur[train_idx])
        kpts_fin, des_fin = [], []
        kpts_fin = np.array(kpts_fin_temp)
        des_fin = np.array(des_fin_temp)
        kpts_cur, des_cur = [], []
        kpts_cur = np.array(kpts_cur_temp)
        des_cur = np.array(des_cur_temp)
        print("Final Keypoints:", len(kpts_fin))
        frame[k] = cv2.drawKeypoints(frame[k], kpts_cur, None, color = (255, 0, 0), flags=0)
        frame[k] = cv2.drawKeypoints(frame[k], kpts_fin, None, color=(0, 255, 0), flags=0)
        for i in range(len(kpts_fin)):
            pt1 = np.int32(kpts_fin[i].pt)
            pt2 = np.int32(kpts_cur[i].pt)
            frame[k] = cv2.line(frame[k], pt1, pt2, (0, 0, 255), thickness=2)
        cv2.imshow("frame", frame[k])
        out.write(frame[k])
        if k == 0:
            save_kpt_des(kpts_fin, des_fin, filename)
        # Wait for Esc key to stop
        if cv2.waitKey(1) == 27:
            # De-allocate any associated memory usage
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    frame_kpt, frame_des, frames = extract_keypoints("demo.mp4")
    for i in range(int(len(frames)/INTERVAL)):
        print("Interval", i)
        analyze_kpt_des(frames, frame_kpt, frame_des, "demo_kpt_des/demo_kpt_des%d.yml"%(i+1), "demo_kpt_des/demo%d.mp4"%(i+1))
        frames = frames[-(len(frames)-INTERVAL):]
        frame_kpt = frame_kpt[-(len(frame_kpt)-INTERVAL):]
        frame_des = frame_des[-(len(frame_des)-INTERVAL):]