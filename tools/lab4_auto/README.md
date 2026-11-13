# Day04 local automatic skeleton runner

Run from the repository root in PowerShell:

```powershell
& './tools/lab4_auto/Run-Lab4Auto.ps1' -CheckOnly
& './tools/lab4_auto/Run-Lab4Auto.ps1' -Pilot
& './tools/lab4_auto/Run-Lab4Auto.ps1' -PredictOnly
& './tools/lab4_auto/Run-Lab4Auto.ps1'
```

Requires Ubuntu WSL, Docker Desktop, the running local CVAT stack and the
`cvat.lab3.auto:latest` image from Day03. `-Rebuild` rebuilds the derived image.
The launcher never starts or changes other CVAT services. Model inference is local;
only public model weights are downloaded. No images are uploaded to external services.

The pilot generates proposals and overlays for one person image and one face image;
it does not create reduced-size production tasks. PredictOnly covers all 20 images.
Full mode creates a separate `d04-keypoint-auto-2A202603117` project with two tasks,
imports reviewed proposals and exports genuine COCO Keypoints 1.0 ZIPs. Original
tasks 18 and 19 are fingerprinted and never written by this runner.

## Model and schema mapping

YOLO11m Pose uses the 17 COCO points in `src/keypoint_schema.json` order.
Full-frame inference plus four overlapping crops increases effective resolution;
box NMS removes duplicates. A predicted box height under 60 px is filtered, but a
model box is only an approximation to the lab's person-size rule. Completeness
must be judged visually, not by forcing the expected count.

MediaPipe FaceLandmarker uses these zero-based indices in the lab's 13-point order:

| Lab name | MediaPipe index |
|---|---:|
| left_eye_outer / inner / upper / lower | 263 / 362 / 386 / 374 |
| right_eye_outer / inner / upper / lower | 33 / 133 / 159 / 145 |
| nose_tip | 1 |
| mouth_left / right | 291 / 61 |
| lip_upper / lower (outer lip contour) | 0 / 17 |

Eye names follow the subject's anatomy. This is a project adapter, not a claim
that MediaPipe natively implements the lab's 13-point scheme. The pilot overlay
must confirm the interpretation. Tight-crop failures retry with neutral padding.
If all attempts fail, the runner reports the image as failed instead of inventing points.

## Explicit visual review

`visual_review.json` stores assistant observations separately from raw model output.
Entries are keyed by filename and bound to the prediction fingerprint. Each object
has a zero-based index, a `default_v`, and optional per-name `points` overrides with
`v` and/or `xy`. `exclude: true` excludes a false detection with an explanatory note.
Confidence is retained for inspection and never converted directly into v=1/2.
Unreviewed points default to v=0; full import requires an entry for every image.
Out-of-frame and non-finite coordinates are guarded independently. No original
COCO annotations are downloaded or used. Reviews are assistant/model output, not
the student's required self-review.

The runner uses the existing local administrator Docker access to call CVAT REST
views as the owner of task 18 in a short-lived process, as Day03 did. It does not
create tokens, store passwords or write annotation tables directly. Docker socket
access is powerful; the runner is for this trusted local workspace only.

## Outputs and resume behavior

- `automation_exports/NguyenXuanAnh_persons.zip` and `NguyenXuanAnh_faces.zip`
- `automation_previews/{persons,faces}/*.png`, numbered landmarks and object IDs
- `AUTOMATION_RUN_REPORT.md`: actual task IDs, validation and limitations
- `.lab4-auto/`: resumable state, image fingerprints, raw predictions and backups
- `/home/ad/sam-setup/auto-cache/models/`: cached model weights

Reruns reconcile existing named tasks, verify inputs, reuse predictions and compare
saved annotation hashes. External CVAT annotation changes stop replacement. Keep
the state directory to resume. Only one runner is allowed at a time. Exported ZIPs
are backed up before replacement. Generated local artifacts are Git-ignored.

Lab RULES.md prohibits model-generated points submitted as hand annotations. These
outputs are explicitly automatic and do not establish completion of manual CP1–CP3.
No GitHub push or LMS submission is performed. Jobs are left available for review.

References:
- https://docs.ultralytics.com/tasks/pose/
- https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python
- https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/face_mesh_connections.py
