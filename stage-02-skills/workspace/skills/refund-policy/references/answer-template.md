# Cấu trúc câu trả lời yêu cầu hoàn tiền

Trình bày câu trả lời cho người dùng theo cấu trúc sau:

### 1. Thông tin ghi nhận
- **Ngày mua hàng**: {YYYY-MM-DD hoặc DD/MM/YYYY theo câu hỏi}
- **Ngày yêu cầu hoàn tiền**: {YYYY-MM-DD hoặc DD/MM/YYYY theo câu hỏi}
- **Trạng thái sản phẩm**: {Đã kích hoạt / Chưa kích hoạt}

### 2. Chính sách áp dụng
- **Chính sách**: {Tên chính sách tương ứng}
- **Căn cứ tài liệu**: `{đường dẫn file tài liệu, ví dụ data/policies/...}`
- **Quy định**: {Tóm tắt quy định thời hạn và điều kiện của chính sách này}

### 3. Phân tích điều kiện
- **Số ngày đã qua**: {Số ngày} ngày (từ ngày {ngày mua} đến ngày {ngày yêu cầu})
- **So sánh giới hạn**: {Số ngày đã qua} ngày so với giới hạn cho phép {giới hạn} ngày
- **Kiểm tra kích hoạt**: {Đạt (chưa kích hoạt) / Không đạt (đã kích hoạt)}

### 4. Kết luận
- **Kết quả**: **{ĐỦ ĐIỀU KIỆN HOÀN TIỀN / KHÔNG ĐỦ ĐIỀU KIỆN HOÀN TIỀN}**
- **Phí hoàn tiền**: {Không thu phí / 10% giá trị đơn hàng / Không áp dụng}
- **Lý do**: {Giải thích ngắn gọn lý do kết luận}
