# NeuraLog Attendance Fixes TODO

## Plan Steps:

- [x] 1. Install deps: `pip install mediapipe opencv-python-headless`
- [x] 2. Fix `students/views.py` attendance_report date_from/date_to 'None' handling.
- [ ] 3. Update `students/views.py` take_attendance_submit: always liveness, multi-face recognition/marking.
- [ ] 4. Add `students/utils.py` multi-face utils.
- [ ] 5. Update `students/templates/students/take_attendance.html`: remove fallback, add loading/toasts.
- [ ] 6. Ensure `recognition/liveness.py` complete (MediaPipe EAR).
- [ ] 7. Test: report export (no crash), multi-attendance.

**Complete when all checked.**
