---
name: refund-policy
description: Tra cứu, chọn và áp dụng chính sách hoàn tiền theo ngày mua và thông tin đơn hàng của khách hàng. Dùng khi người dùng hỏi về hoàn tiền, chính sách hoàn tiền, điều kiện hoặc phí hoàn trả.
---

# Refund policy

Hướng dẫn tra cứu, kiểm tra điều kiện và trả lời yêu cầu hoàn tiền của khách hàng.

## Nguyên tắc quan trọng

1. **Khám phá tài liệu động**: Không cố định tên file chính sách. Luôn dùng `list_files` để liệt kê thư mục `data/policies/`, sau đó dùng `read_file` để đọc nội dung từng chính sách tìm được nhằm xác định phạm vi hiệu lực và các điều kiện.
2. **Kiểm tra thông tin bắt buộc trước khi kết luận**:
   Yêu cầu phải có đủ 3 thông tin:
   - **Ngày mua hàng** (purchase date)
   - **Ngày yêu cầu hoàn tiền** (refund request date) nêu trong câu hỏi (dùng ngày trong câu hỏi, không dùng ngày hiện tại của máy)
   - **Trạng thái kích hoạt sản phẩm** (đã kích hoạt hay chưa)
   
   ⚠️ **NẾU THIẾU BẤT KỲ THÔNG TIN NÀO** (ví dụ thiếu trạng thái kích hoạt, hoặc thiếu ngày mua/ngày yêu cầu):
   **DỪNG LẠI NGAY VÀ HỎI NGƯỜI DÙNG** để làm rõ. Tuyệt đối **KHÔNG TỰ GIẢ ĐỊNH** (ví dụ: không được tự suy đoán "chưa kích hoạt").

## Các bước thực hiện

1. **Kiểm tra thông tin đầu vào (BƯỚC QUAN TRỌNG NHẤT - KIỂM TRA TRƯỚC TIÊN)**:
   - Kiểm tra câu hỏi của người dùng có đủ 3 thông tin sau không:
     1. Ngày mua hàng
     2. Ngày yêu cầu hoàn tiền
     3. Trạng thái kích hoạt (người dùng có nói rõ "chưa kích hoạt" hoặc "đã kích hoạt" không)
   - ⚠️ **NẾU THIẾU THÔNG TIN (Đặc biệt là thiếu trạng thái kích hoạt, ví dụ người dùng chỉ hỏi "Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026"):**
     - **DỪNG LẠI NGAY LẬP TỨC.**
     - **TUYỆT ĐỐI KHÔNG TỰ GIẢ ĐỊNH LÀ "CHƯA KÍCH HOẠT".**
     - **KHÔNG KẾT LUẬN HOÀN TIỀN.**
     - Trả lời người dùng để hỏi làm rõ trạng thái kích hoạt: hỏi người dùng xem sản phẩm đã được kích hoạt hay chưa.
   - **CHỈ KHI CÓ ĐỦ CẢ 3 THÔNG TIN** thì mới thực hiện tiếp Bước 2, 3, 4 bên dưới.

2. **Tìm tài liệu chính sách (khi đã đủ thông tin)**:
   - Gọi `list_files(path="data/policies")` để lấy danh sách tất cả các file chính sách đang có trong thư mục.
   - Với mỗi file tìm thấy, dùng `read_file` để đọc nội dung và xác định phạm vi ngày áp dụng cũng như quy định hoàn tiền (thời hạn, phí, điều kiện kích hoạt).

3. **Chọn chính sách áp dụng theo NGÀY MUA HÀNG (Purchase Date)**:
   - ⚠️ CHỈ DỰA VÀO NGÀY MUA HÀNG để chọn phiên bản chính sách. Tuyệt đối KHÔNG dùng ngày yêu cầu hoàn tiền để chọn chính sách.
   - Đối chiếu ngày mua hàng của khách với phạm vi hiệu lực của các chính sách vừa đọc:
     - Nếu Ngày mua trước 2026-10-01 (ví dụ tháng 9/2026 trở về trước, như ngày 28/09/2026): BẮT BUỘC áp dụng chính sách trước tháng 10 (thời hạn 7 ngày, phí 10%, chưa kích hoạt).
     - Nếu Ngày mua từ 2026-10-01 trở đi: Áp dụng chính sách từ tháng 10 (thời hạn 14 ngày, không phí, chưa kích hoạt).

4. **Tính toán số ngày và xét điều kiện**:
   - Số ngày đã qua = (Ngày yêu cầu hoàn tiền) - (Ngày mua hàng) tính theo số ngày lịch.
   - Ví dụ: Mua ngày 28/09/2026, yêu cầu 06/10/2026 -> Đã qua 8 ngày (> 7 ngày giới hạn) -> KHÔNG ĐỦ ĐIỀU KIỆN HOÀN TIỀN.
   - Quy ước: Bằng đúng giới hạn ngày quy định vẫn đủ điều kiện về thời gian.
   - Xét trạng thái kích hoạt: Nếu đã kích hoạt, không đủ điều kiện hoàn tiền.
   - Kết luận đủ/không đủ điều kiện và mức phí (nếu đủ điều kiện).

5. **BẮT BUỘC ĐỌC TEMPLATE ĐỂ ĐỊNH DẠNG CÂU TRẢ LỜI**:
   - ⚠️ **QUY TẮC BẮT BUỘC:** Sau khi đọc các file chính sách, bạn **CHƯA ĐƯỢC PHÉP TRẢ LỜI NGAY**. Bạn **PHẢI GỌI TIẾP `read_file(path="skills/refund-policy/references/answer-template.md")`** để nạp cấu trúc mẫu.
   - Sau khi đọc xong template, xuất câu trả lời tuân thủ nghiêm ngặt 4 phần được quy định trong template:
     1. Thông tin ghi nhận
     2. Chính sách áp dụng
     3. Phân tích điều kiện
     4. Kết luận
