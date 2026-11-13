# Day04 — Kết quả tự động hóa

Nhãn sinh từ model, được trợ lý xem overlay; không phải bài gán tay hoặc tự review của học viên.
Kết quả kiểm cấu trúc không chứng minh tọa độ và visibility chính xác. Không push/nộp LMS.

Cập nhật UTC+7: 2026-11-12T18:12:59.901491+07:00

```json
{
  "version": "lab4-v3",
  "pose": "yolo11m-pose.pt",
  "imgsz": 1280,
  "full_imgsz": 640,
  "conf": 0.2,
  "nms": 0.5,
  "threads": 4,
  "face": "mediapipe-face-landmarker-float16-v1"
}
```

| Bộ ảnh | Task / Job | Skeleton | Trạng thái |
|---|---|---:|---|
| persons | 20 / 20 | 23 | exported |
| faces | 21 / 21 | 8 | exported |

[Job persons](http://localhost:8080/tasks/20/jobs/20)

ZIP: `automation_exports/NguyenXuanAnh_persons.zip`


[Job faces](http://localhost:8080/tasks/21/jobs/21)

ZIP: `automation_exports/NguyenXuanAnh_faces.zip`


Hai task gốc 18/19 giữ nguyên: True

Thời gian suy luận thực tế theo cache (giây): {'persons': 72.62, 'faces': 0.81}
Không bao gồm thời gian tải/cài model và review của trợ lý.

## Quan sát của trợ lý theo ảnh

- `000000023424.jpg`: Bốn đề xuất người gồm người quay lưng và ba người nhỏ phía sau. Giữ vì bbox cao 64–196 px; nhóm người nhỏ sát ngưỡng và bị che cần người dùng/coach đối chiếu, số lượng không được ép theo tổng 20 của README. Mặt người quay lưng v=0.
- `000000043500.jpg`: Hai người làm việc trên tàu. Người ngoài quay lưng; mặt không thấy. Cầu thang và thanh chắn che một phần chân/tay. Vị trí hông và đầu gối dưới quần còn là ước lượng.
- `000000057978.jpg`: Một người dưới ô; chân bị đá che một phần. Chi tiết mặt tối và nhỏ, độ chính xác mắt/tai còn hạn chế.
- `000000103970.jpg`: Một người lướt sóng; lượt 640 khắc phục tách thân/chân ở lượt 1280. Hai cổ tay và hai cổ chân nằm trên người, không còn skeleton trùng.
- `000000150192.jpg`: Người trước bị bàn che từ hông xuống và che cổ tay: đặt v=0. Chỉnh ba điểm mặt bị model đặt cao. Người ngồi phía sau sát ngưỡng 60 px, chi dưới bàn khó xác định; người bên cạnh nhỏ và bị che có nguy cơ bỏ sót. Không gán người trên màn hình.
- `000000205650.jpg`: Một nhân viên trên cửa tàu. Hai bàn tay gần nhau; hông dưới áo và tai phía xa cần suy đoán vị trí.
- `000000240340.jpg`: Một người ngồi xe máy. Chân bên phải của người bị xe che một phần; giữ điểm gối, đánh dấu cổ chân bị che.
- `000000261732.jpg`: Một vận động viên tennis trên không; tay trái gập gần ngực. Giữ trái/phải theo người; tai phía xa khó thấy.
- `000000332273.jpg`: Ba cầu thủ chồng lên nhau. Loại trùng bằng ảnh đầy đủ; mặt người trượt bị mũ che. Chân cầu thủ lao người bị người trước che; một số khớp v=0. Đây là ảnh khó nhất, các điểm khuất và chân bắt chéo chưa có ground truth để xác nhận.
- `000000461389.jpg`: Ba người, gồm hai người bị cắt phần trên. Bỏ cờ thấy cho đầu ngoài khung; người phía sau chỉ thấy rõ phần chân. Không kéo điểm về mép ảnh.
- `000000469061.jpg`: Hai người trượt tuyết. Mắt người lớn sau kính, tai dưới mũ; chân phải người lớn bị trẻ che, không đủ cơ sở đặt. Chỉnh chân trái nhìn thấy từ ảnh. Trẻ nghiêng sang phải ảnh, phía xa bị mũ che.
- `000000516902.jpg`: Hai người. Vận động viên phía trước có đủ thân/chân; người phía sau bị cắt đầu và bị che từ hông xuống. Các chân model dự đoán xuyên sang người trước được đặt v=0.
- `face_141135.jpg`: Mắt gần khép; các điểm mí nằm trên đường mí nhìn thấy. Không đổi mắt khép thành occluded.
- `face_145621.jpg`: Mặt nghiêng sang trái ảnh, cả hai mắt còn nhìn thấy. Râu làm mép môi kém rõ; điểm môi dưới còn sai số model.
- `face_279764.jpg`: Tóc sát bên mặt; 13 điểm vẫn nhìn thấy. Ảnh mờ nên mép mí chỉ là ước lượng model.
- `face_324513.jpg`: Kính râm phản quang che cả hai mắt: tám điểm mắt v=1; vị trí ước lượng theo tròng kính.
- `face_3348.jpg`: Mặt gần thẳng, 13 điểm theo mắt và mép ngoài môi; left nằm bên phải ảnh.
- `face_421231.jpg`: Mặt hơi nghiêng/cúi, hai mắt và miệng đều nhìn thấy; ánh xạ trái/phải phù hợp.
- `face_442231.jpg`: Mặt nghiêng, hai mắt và khóe miệng còn trong ảnh; thức ăn chưa che miệng.
- `face_514826.jpg`: Kính trong: giữ các điểm mắt v=2 vì còn thấy mắt; ảnh tối và phản chiếu gây sai số.

## Kiểm file xuất

```text

=== automation_exports/NguyenXuanAnh_persons.zip (label `person`) ===
  [CẢNH BÁO] 000000023424.jpg #2: các điểm chỉ trải cao 50 px (< 60 px). Người dưới 60 px không gán; nếu người cao hơn nhưng bị cắt khung thì bỏ qua cảnh báo này.
  [CẢNH BÁO] 000000150192.jpg #1: các điểm chỉ trải cao 43 px (< 60 px). Người dưới 60 px không gán; nếu người cao hơn nhưng bị cắt khung thì bỏ qua cảnh báo này.
  [CẢNH BÁO] 000000332273.jpg #3: cặp ankle nằm ngược phía so với các cặp còn lại. Có thể đổi trái/phải một cặp (`lr_swap`), hoặc tay / chân bắt chéo thật: kiểm lại.

=== automation_exports/NguyenXuanAnh_faces.zip (label `face`) ===

----- TÓM TẮT (dán vào báo cáo mục 5) -----
- File person: NguyenXuanAnh_persons.zip
  Số ảnh: 12 · số skeleton `person`: 23 · mỗi annotation 51 số
  Skeleton theo ảnh: 000000023424=4, 000000043500=2, 000000057978=1, 000000103970=1, 000000150192=2, 000000205650=1, 000000240340=1, 000000261732=1, 000000332273=3, 000000461389=3, 000000469061=2, 000000516902=2
  Cờ v: v=2 242 (62%) · v=1 79 (20%) · v=0 70 (18%)
  num_keypoints trung bình: 14.0
- File face: NguyenXuanAnh_faces.zip
  Số ảnh: 8 · số skeleton `face`: 8 · mỗi annotation 39 số
  Skeleton theo ảnh: face_141135=1, face_145621=1, face_279764=1, face_324513=1, face_3348=1, face_421231=1, face_442231=1, face_514826=1
  Cờ v: v=2 96 (92%) · v=1 8 (8%) · v=0 0 (0%)
  num_keypoints trung bình: 13.0
- Ghi chú: 70 điểm v = 0 vẫn mang tọa độ cũ (CVAT 2.x xuất như vậy; chuẩn COCO ghi 0, 0). Không phải lỗi: điểm v = 0 bị bỏ qua khi huấn luyện và khi chấm.
- Số [LỖI]: 0 · số [CẢNH BÁO]: 3
Kết quả: ĐẠT (đọc lại từng cảnh báo ở trên)

```

## Phiên bản runtime

```json
{
  "ultralytics": "8.4.210",
  "mediapipe": "0.10.21",
  "torch": "2.14.1+cpu",
  "numpy": "1.26.4",
  "docker": "7.2.0",
  "opencv-python": "4.11.0.86",
  "opencv-contrib-python": "4.11.0.86",
  "onnx": "1.17.0"
}
```

## SHA-256 model

```json
{
  "yolo11m-pose.pt": "29b17eaf3a3117cbea906090dbedf9159f7c6a49db58ec8b99ed2dfde1cf6eb2",
  "face_landmarker.task": "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff"
}
```

## Kiểm chứng runner

```json
{
  "persons": {
    "images": 12,
    "skeletons_verified": 23,
    "max_coordinate_rounding_px": 0.011
  },
  "faces": {
    "images": 8,
    "skeletons_verified": 8,
    "max_coordinate_rounding_px": 0.011
  },
  "core_tests": ".......\n----------------------------------------------------------------------\nRan 7 tests in 0.001s\n\nOK",
  "dependencies": "No broken requirements found.",
  "rerun_same_tasks_annotations_zip": true,
  "originals_unchanged": true
}
```
