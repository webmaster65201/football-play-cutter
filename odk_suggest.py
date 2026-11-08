"""Conservative, experimental ODK suggestions from pre-snap jersey color layout.

Not a trained football model. Kicking cannot be reliably inferred by this method.
Unknown attacking direction => abstain, rather than fabricate labels.
"""
import cv2
import numpy as np


def suggest_odk(video, start, end, direction='unknown'):
    """Return (ODK, explanation). Direction is Southside's offensive attack direction.

    A coarse color-layout heuristic, not verified possession recognition. White and
    blue pixel masks are sampled in the central field. No special-teams prediction.
    """
    if direction not in ('left', 'right'):
        return '?', 'Needs review: attacking direction unknown; colors alone cannot establish possession'
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        return '?', 'Needs review: video could not be opened'
    # Early frames, before the majority of active play, may show pre-snap formations.
    moments = [start + x for x in (0.4, 1.2, 2.0) if start + x < end]
    scores = []
    try:
        for t in moments:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok: continue
            frame = cv2.resize(frame, (480, 270))
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Exclude scoreboard/top banners and most of the bottom sideline.
            roi = hsv[48:224, 35:445]
            # White jersey mask (bright, low saturation) and blue jersey mask.
            white = ((roi[:,:,1] < 65) & (roi[:,:,2] > 165)).astype('uint8')
            blue = ((roi[:,:,0] >= 94) & (roi[:,:,0] <= 135) &
                    (roi[:,:,1] > 75) & (roi[:,:,2] > 45)).astype('uint8')
            kernel = np.ones((3,3),np.uint8)
            centers=[]
            for mask in (white, blue):
                mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
                num,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,8)
                blobs=[(centroids[i][0],stats[i,cv2.CC_STAT_AREA]) for i in range(1,num)
                       if 12 <= stats[i,cv2.CC_STAT_AREA] <= 550]
                if len(blobs)<3:
                    centers.append(None)
                else:
                    centers.append(float(np.median([x for x,a in blobs])))
            if None not in centers:
                scores.append(centers[0]-centers[1])
    finally:
        cap.release()
    if len(scores)<2:
        return '?', 'Needs review: jersey colors not sufficiently distinguishable'
    delta=float(np.median(scores))
    if abs(delta)<65 or np.sign(scores[0]) != np.sign(scores[-1]):
        return '?', 'Needs review: no stable team separation in sampled frames'
    # The offense is *often* on the backfield side of the defensive front.
    # This is a weak geometric clue, not a possession determination.
    white_right=delta>0
    white_backfield = white_right if direction=='left' else not white_right
    guess='O' if white_backfield else 'D'
    return guess, 'LOW CONFIDENCE color-layout suggestion; verify possession and formation manually'
