# Checklist hoàn thiện Lab Day04

Kiểm tra lúc: 2026-11-12T21:34:30+07:00 (UTC+7).

## Kết quả hiện tại

**Hai ZIP mới đạt kiểm tra cấu trúc: 0 lỗi, 3 cảnh báo. Chưa đủ bằng chứng để đánh dấu toàn bộ bài đã hoàn tất.**
Bản người có 12 ảnh / 21 skeleton; bản mặt có 8 ảnh / 8 skeleton. Đây là kết quả của ZIP bạn vừa đặt trong `src/exports/`, không dùng số liệu 23 người của bản tự động cũ.

## Việc trợ lý đã làm trong lượt này

- [x] Tìm và đọc hai ZIP trong `src/exports/`; không sửa nội dung hoặc ghi đè ZIP.
- [x] Chạy nguyên script `src/check_submission.py` của lab.
- [x] Đối chiếu đúng danh sách ảnh với `assignment.json`.
- [x] Kiểm tên/thứ tự 17 và 13 điểm, tập cạnh 19 và 13 cạnh, mảng 51/39 số.
- [x] Kiểm `num_keypoints` của toàn bộ 29 annotation bằng số điểm có v>0.
- [x] Kiểm ZIP không lỗi CRC và không chứa ảnh gốc.
- [x] Đọc chi tiết JSON của 2 người và 1 mặt; điền bằng chứng vào mục 5 báo cáo.
- [x] So sánh nội dung nhãn với bản tự động cũ: 9 ảnh người và 1 ảnh mặt có thay đổi.
- [x] Tạo [báo cáo cá nhân bản nháp](report/individual/2A202603117_NguyenXuanAnh.md); giữ mẫu gốc.
- [x] Để thời gian, mục 3/4/7 và nhận xét cá nhân là **CHỜ BẠN ĐIỀN**, theo yêu cầu của bạn.
- [x] Tạo file checklist này để bạn rà lại các thao tác và giới hạn.
- [ ] Xác minh completed và chụp màn hình CVAT: Docker hiện không kết nối được.
- [ ] Commit/push/LMS: chưa thực hiện; báo cáo và ảnh minh chứng còn thiếu.

## Ba cảnh báo cần xử lý trên CVAT

| Ảnh / annotation theo script | Cảnh báo | Việc cần làm |
|---|---|---|
| `000000150192.jpg #2` | Điểm trải cao 43 px | Kiểm người thực sự dưới 60 px hay chỉ phần điểm còn thấy dưới 60 px vì bị che. Sửa hoặc ghi rõ lý do giữ. |
| `000000332273.jpg #2` | Hai cổ chân ngược phía các cặp khác | Lần theo hông → gối → cổ chân; xác nhận chân bắt chéo thật hay đổi trái/phải. |
| `000000469061.jpg #2` | Khuỷu/cổ tay ngược phía các cặp khác | Lần theo vai → khuỷu → cổ tay từng người; xác nhận tư thế thật hay nhầm nhãn. |

Chỉ số # trong bảng là số annotation script in ra trong ảnh, không phải ID object trên giao diện CVAT. Chưa đánh dấu ba cảnh báo này đã được giải quyết.

## Những mục còn cần hoàn thiện theo README / CHECKPOINTS / SUBMISSION

1. Điền thông tin còn thiếu và thời gian thực tế trong báo cáo cá nhân.
2. Điền bảng ca khó (mục 3), tự review ít nhất 8 dòng (5 ảnh người, gồm ít nhất 2 ảnh back/crowd; 3 ảnh mặt) và tự đánh giá (mục 7).
3. Khởi động Docker Desktop/CVAT để kiểm lại ba cảnh báo và trạng thái job.
4. Chụp đủ 4 ảnh thật vào `report/individual/images/`: `1_label_person.png`, `2_nguoi_quay_lung.png`, `3_mat_phong_to.png`, `4_json_export.png`. Overlay tự động không được coi là ảnh chụp giao diện.
5. Trên đúng job bạn đã sửa, dùng Menu → Finish the job khi đã hoàn tất review. Hiện assignment trỏ [job 20](http://localhost:8080/tasks/20/jobs/20) và [job 21](http://localhost:8080/tasks/21/jobs/21); đây là ID đọc từ file, chưa xác nhận live ở lượt này.
6. Nếu sửa nhãn tiếp, export lại COCO Keypoints 1.0, tắt Save images và kiểm lại hai ZIP trước khi nộp.
7. Rà file bằng `git status --short` rồi chọn file cần commit; sau khi đủ báo cáo/ảnh/nhãn thì commit, push và nộp link repo trên LMS. Không dùng `git add -A` khi chưa rà file dư.

## Điểm cần đối chiếu về assignment và nguồn nhãn

- MSSV, tên và bộ ảnh trong `assignment.json` khớp lần setup đầu và hai ZIP hiện tại.
- Task/job trong file hiện là **20/21**, trong khi log setup ban đầu là **18/19**. Trường project vẫn là `d04-keypoint` và tên task trong file không có `auto`, khác project/task tự động đã tạo ở lượt trước. File có thêm `assignment.json.save` với nội dung JSON tương đương.
- Trợ lý giữ nguyên cả hai file assignment. RULES.md không cho sửa assignment bằng tay; cần trao đổi coach về mapping task này trước khi nộp, không tự đổi tiếp cho khớp.
- Nguồn ban đầu của nhãn là model + review của trợ lý; ZIP hiện tại có chỉnh sửa sau đó. Quy định gán tay vẫn cần được coach làm rõ; đạt script không đồng nghĩa đạt yêu cầu này.
- Tổng 21 người khác con số 20 trong README. Không tự xóa một người chỉ để khớp số; xác nhận từng người thật và ngưỡng 60 px.

## Bằng chứng file đã kiểm

| File | Dung lượng byte | SHA-256 |
|---|---:|---|
| `src/exports/NguyenXuanAnh_persons.zip` | 12527 | `9596742060ac2968a838b92e7b97319f3623dc70dc0b7620e718ac47ba2e8bb1` |
| `src/exports/NguyenXuanAnh_faces.zip` | 5443 | `4a399520171dfe40b46ca3c4fc618c89f0036f0e904cd789f05618b0aad13a59` |

Các hash giúp bạn xác nhận checklist đang nói về đúng bản ZIP. Nếu export lại, cần chạy kiểm tra lại.

## Thay đổi so với bản tự động cũ

| Bộ | Ảnh | Skeleton cũ → mới |
|---|---|---|
| persons | `000000023424.jpg` | 4 → 2 |
| persons | `000000043500.jpg` | 2 → 2 |
| persons | `000000103970.jpg` | 1 → 1 |
| persons | `000000150192.jpg` | 2 → 2 |
| persons | `000000205650.jpg` | 1 → 1 |
| persons | `000000240340.jpg` | 1 → 1 |
| persons | `000000261732.jpg` | 1 → 1 |
| persons | `000000332273.jpg` | 3 → 3 |
| persons | `000000469061.jpg` | 2 → 2 |
| faces | `face_145621.jpg` | 1 → 1 |

Các ảnh giữ số lượng vẫn có thay đổi tọa độ/cờ trong mảng keypoints. Không suy luận lý do sửa từ sự khác biệt file.

## Lệnh kiểm lại

Chạy trong thư mục gốc repo, dùng `python3` nếu đang ở WSL:

```powershell
python src/check_submission.py --persons src/exports/NguyenXuanAnh_persons.zip --faces src/exports/NguyenXuanAnh_faces.zip
```

## Log kiểm tra thực tế

```text
=== src\exports\NguyenXuanAnh_persons.zip (label `person`) ===
  [CẢNH BÁO] 000000150192.jpg #2: các điểm chỉ trải cao 43 px (< 60 px). Người dưới 60 px không gán; nếu người cao hơn nhưng bị cắt khung thì bỏ qua cảnh báo này.
  [CẢNH BÁO] 000000332273.jpg #2: cặp ankle nằm ngược phía so với các cặp còn lại. Có thể đổi trái/phải một cặp (`lr_swap`), hoặc tay / chân bắt chéo thật: kiểm lại.
  [CẢNH BÁO] 000000469061.jpg #2: cặp elbow, wrist nằm ngược phía so với các cặp còn lại. Có thể đổi trái/phải một cặp (`lr_swap`), hoặc tay / chân bắt chéo thật: kiểm lại.

=== src\exports\NguyenXuanAnh_faces.zip (label `face`) ===

----- TÓM TẮT (dán vào báo cáo mục 5) -----
- File person: NguyenXuanAnh_persons.zip
  Số ảnh: 12 · số skeleton `person`: 21 · mỗi annotation 51 số
  Skeleton theo ảnh: 000000023424=2, 000000043500=2, 000000057978=1, 000000103970=1, 000000150192=2, 000000205650=1, 000000240340=1, 000000261732=1, 000000332273=3, 000000461389=3, 000000469061=2, 000000516902=2
  Cờ v: v=2 222 (62%) · v=1 65 (18%) · v=0 70 (20%)
  num_keypoints trung bình: 13.7
- File face: NguyenXuanAnh_faces.zip
  Số ảnh: 8 · số skeleton `face`: 8 · mỗi annotation 39 số
  Skeleton theo ảnh: face_141135=1, face_145621=1, face_279764=1, face_324513=1, face_3348=1, face_421231=1, face_442231=1, face_514826=1
  Cờ v: v=2 96 (92%) · v=1 8 (8%) · v=0 0 (0%)
  num_keypoints trung bình: 13.0
- Ghi chú: 70 điểm v = 0 vẫn mang tọa độ cũ (CVAT 2.x xuất như vậy; chuẩn COCO ghi 0, 0). Không phải lỗi: điểm v = 0 bị bỏ qua khi huấn luyện và khi chấm.
- Số [LỖI]: 0 · số [CẢNH BÁO]: 3
Kết quả: ĐẠT (đọc lại từng cảnh báo ở trên)
```

## Git và bàn giao

- Nhánh hiện tại: `main`; origin đã trỏ đúng repo cá nhân.
- [Repository](https://github.com/xanhhangreal/K5-L2-DAY04-NguyenXuanAnh-2A202603117-KeypointPose). Chưa xác minh nội dung remote, quyền chấm bài hoặc trạng thái LMS.
- Không đưa `.lab4-auto/`, `automation_previews/`, ảnh gốc, mật khẩu hoặc file sao lưu `assignment.json.save` vào bài nộp.
- `AUTOMATION_RUN_REPORT.md` mô tả lượt tự động trước; số liệu ZIP mới nằm trong checklist này và báo cáo cá nhân.
- Các file mới/sửa ở lượt này: checklist này, báo cáo cá nhân bản nháp và quy tắc bỏ qua file backup trong `.gitignore`. Hai ZIP và assignment được giữ nguyên.
