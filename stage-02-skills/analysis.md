# Báo cáo phân tích bài Block 1 — Stage 02

**Đề tài:** Tra cứu chính sách hoàn tiền đúng phiên bản bằng tool và skill.  

## 1. Mục tiêu và phạm vi

Stage 02 kết hợp khả năng tìm tài liệu của tool `list_files` với quy trình nghiệp vụ trong skill `refund-policy`. Agent cần tự tìm và đọc tài liệu, chọn chính sách theo **ngày mua**, kiểm tra điều kiện hoàn tiền, rồi trả lời có căn cứ. Khi tên tài liệu thay đổi nhưng nội dung giữ nguyên, kết luận nghiệp vụ phải không thay đổi.

Báo cáo tập trung vào yêu cầu kỹ thuật của Stage 02, kết quả kiểm tra tool, từng tình huống nghiệp vụ và bằng chứng cần đối chiếu trong trace. 


## 2. Yêu cầu kỹ thuật và quy tắc nghiệp vụ

### 2.1. Tool tìm tài liệu

| Nội dung | Yêu cầu theo đề bài |
| --- | --- |
| Phạm vi liệt kê | `list_files(path: str)` chỉ liệt kê các mục trực tiếp trong thư mục, không duyệt đệ quy. |
| Thông tin từng mục | Có tên, đường dẫn tương đối với workspace và loại `file` hoặc `directory`. |
| Thứ tự kết quả | Sắp xếp theo tên để kết quả ổn định. |
| Xử lý lỗi | Trả lỗi rõ ràng khi đường dẫn không tồn tại hoặc trỏ đến file; không trả danh sách rỗng như một thư mục hợp lệ. |
| Giới hạn truy cập | Chỉ truy cập trong workspace, kể cả khi có `..`, đường dẫn tuyệt đối hoặc symlink dẫn ra ngoài. |
| Tích hợp agent | Tool xuất hiện trong schema tools gửi model; agent dùng `list_files` để tìm và `read_file` để đọc tài liệu. |
| Tính tổng quát | Không cố định tên file, nội dung chính sách hoặc đáp án trong system prompt hay mã nguồn tool. |

Đường dẫn agent truyền vào tool để tìm chính sách là `data/policies/`. Tiền tố `workspace/` thuộc cấu trúc thư mục của project, không thuộc đường dẫn tương đối truyền vào tool.

Báo cáo trước mô tả tool dùng `_resolve` để xử lý đường dẫn, trả kết quả có `ok`, `path`, `entries` và lỗi có `code`, `message`. Bản đó cũng ghi nhận tool được đăng ký qua `tools/__init__.py` và danh sách `TOOLS` trong `agent.py`. Đây là thông tin đã được báo cáo, chưa phải kết quả đối chiếu mã nguồn trong lần biên tập này. Việc gọi `_resolve` tự nó chưa đủ để xác nhận đầy đủ cách xử lý symlink.

### 2.2. Skill `refund-policy` và reference

Cấu trúc yêu cầu trong Stage 02:

```text
workspace/skills/refund-policy/
├── SKILL.md
└── references/
    └── answer-template.md
```

`SKILL.md` phải có frontmatter gồm `name` và `description`; phần mô tả cần nêu nhiệm vụ và điều kiện sử dụng skill. Quy trình nghiệp vụ cần bao quát:

1. Kiểm tra ngày mua, ngày yêu cầu hoàn và trạng thái kích hoạt. Thiếu thông tin thì hỏi bổ sung trước khi kết luận.
2. Tìm tài liệu trong `data/policies/` bằng tool; sử dụng đường dẫn từ kết quả liệt kê, không đoán hoặc cố định tên file.
3. Đọc nội dung để xác định phạm vi áp dụng và điều kiện hoàn tiền. Tên file giúp định vị; nội dung mới là căn cứ chọn phiên bản.
4. Chọn chính sách theo ngày mua, tính số ngày đã qua và kiểm tra điều kiện thời gian, kích hoạt.
5. Trả lời theo reference và dẫn đường dẫn tài liệu đã đọc.

Reference phải quy định đủ năm thành phần: **chính sách áp dụng; số ngày đã qua; kết luận đủ/không đủ điều kiện; phí nếu đủ điều kiện; đường dẫn tài liệu làm căn cứ**. Skill không yêu cầu Bash hoặc script vì agent Stage 02 chưa có khả năng đó.

### 2.3. Chính sách và cách tính

| Tiêu chí | Chính sách trước tháng 10 | Chính sách từ tháng 10 |
| --- | --- | --- |
| Phạm vi ngày mua | Trước `2026-10-01` | Từ `2026-10-01`, bao gồm ngày này |
| Thời hạn yêu cầu hoàn | Trong 7 ngày kể từ ngày mua | Trong 14 ngày kể từ ngày mua |
| Trạng thái kích hoạt | Không hoàn nếu đã kích hoạt | Không hoàn nếu đã kích hoạt |
| Phí khi đủ điều kiện | 10% giá trị đơn hàng | Không thu phí |
| Đường dẫn ban đầu theo đề bài | `data/policies/policy-before-oct.md` | `data/policies/policy-from-oct.md` |

Các quy tắc quyết định:

- **Chọn phiên bản theo ngày mua.** Ngày yêu cầu hoàn sau mốc đổi chính sách không làm giao dịch mua trước mốc chuyển sang chính sách mới.
- **Số ngày = ngày yêu cầu hoàn − ngày mua**, tính chênh lệch ngày lịch. Không dùng ngày hiện tại của máy, không cộng thêm một ngày để đếm cả hai đầu mốc.
- **Bằng đúng thời hạn vẫn đạt điều kiện thời gian:** 7 ngày với chính sách cũ, 14 ngày với chính sách mới.
- **Đủ điều kiện hoàn** khi chưa kích hoạt và nằm trong thời hạn của chính sách áp dụng. Thiếu dữ liệu thì chưa được kết luận.
- **Phí chỉ xác định cho trường hợp đủ điều kiện.** Không trình bày giao dịch quá hạn như vẫn được hoàn nếu chấp nhận trả phí.

## 3. Kết quả kiểm tra tool trực tiếp

Bảng dưới giữ lại kết quả đã ghi trong báo cáo trước. Các mã lỗi là mã được bản trước mô tả; đề bài yêu cầu lỗi rõ ràng và nhất quán với tool file hiện có, không ấn định chính xác tên mã lỗi.

| Mã | Đầu vào đã báo cáo | Kết quả ghi nhận trong bản trước | Đối chiếu và bằng chứng còn cần |
| --- | --- | --- | --- |
| T1 — Thư mục hợp lệ | `data/policies` | `ok: true`; danh sách có hai file chính sách, sắp xếp theo tên. | Phù hợp về khả năng tìm tài liệu. Cần output đầy đủ để xác nhận tên, đường dẫn, loại và phạm vi không đệ quy. |
| T2 — Đường dẫn là file | `data/note.md` | `ok: false`, mã `NOT_A_DIRECTORY`. | Phù hợp nếu đầu vào thực sự là file tồn tại. Cần tool call và tool result xác nhận lỗi. |
| T3 — Không tồn tại | `data/nonexistent` | `ok: false`, mã `FILE_NOT_FOUND`. | Phù hợp với yêu cầu báo lỗi. Cần cặp tool call/tool result của lần kiểm tra. |
| T4 — Vượt workspace | `../outside` hoặc đường dẫn tuyệt đối | `ok: false`, mã `PATH_OUTSIDE_WORKSPACE`. | Phù hợp với yêu cầu chặn truy cập ngoài workspace. Cần đầu vào thực tế, đặc biệt đường dẫn tuyệt đối cụ thể, và output từ chối. |

**Đánh giá:** kết quả được báo cáo phù hợp với bốn nhóm kiểm tra trực tiếp, nhưng chưa có bản ghi thực thi để xác nhận độc lập. Không suy rộng T4 thành bằng chứng rằng mọi trường hợp symlink đã được kiểm tra. Với đường dẫn tuyệt đối, tiêu chí bắt buộc là không truy cập ngoài workspace sau khi phân giải.

Kiểm tra trực tiếp chỉ dùng dữ liệu giả, không đọc thông tin cá nhân hoặc bí mật. Bảng này không ghi nhận một lần chạy kiểm thử mới trong quá trình viết lại báo cáo.

## 4. Phân tích từng tình huống nghiệp vụ

### 4.1. Trường hợp A — Mua trước ngày đổi chính sách

**Câu hỏi kiểm tra:**

> Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?

Ngày mua `2026-09-28` trước `2026-10-01`, nên áp dụng chính sách cũ. Chênh lệch đến ngày yêu cầu hoàn là **8 ngày**, vượt thời hạn 7 ngày. Sản phẩm chưa kích hoạt nhưng vẫn **không đủ điều kiện hoàn tiền** vì quá hạn. Ngày yêu cầu hoàn nằm trong tháng 10 không làm thay đổi phiên bản áp dụng.

Báo cáo trước ghi nhận agent tải skill, gọi `list_files`, đọc chính sách cũ và reference, rồi kết luận như trên. Kết quả nghiệp vụ đúng theo đề bài; chưa có vị trí trace để xác nhận diễn biến thực thi.

**Câu trả lời kỳ vọng trước khi đổi tên file:**

> Giao dịch áp dụng chính sách hoàn tiền trước tháng 10 vì bạn mua ngày 28/09/2026. Đến ngày yêu cầu hoàn 06/10/2026 đã qua 8 ngày, vượt thời hạn 7 ngày. Vì vậy, dù chưa kích hoạt, bạn không đủ điều kiện hoàn tiền. Căn cứ: `data/policies/policy-before-oct.md`.

**Bằng chứng cần đối chiếu:** kết quả liệt kê chứa tài liệu; kết quả đọc chính sách thể hiện phạm vi trước `2026-10-01` và thời hạn 7 ngày; câu trả lời cuối có 8 ngày, kết luận từ chối và đường dẫn đúng.

### 4.2. Trường hợp B — Mua từ ngày đổi chính sách

**Câu hỏi kiểm tra:**

> Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?

Ngày mua `2026-10-02` thuộc chính sách mới. Chênh lệch đến `2026-10-12` là **10 ngày**, trong thời hạn 14 ngày. Sản phẩm chưa kích hoạt nên **đủ điều kiện hoàn tiền, không thu phí**.

Báo cáo trước ghi nhận agent tải skill, tìm tài liệu, đọc chính sách mới và reference, rồi trả lời đúng kết quả trên. Chưa có vị trí trace để xác nhận nội dung skill và reference đã xuất hiện trong lịch sử.

**Câu trả lời kỳ vọng trước khi đổi tên file:**

> Giao dịch áp dụng chính sách hoàn tiền từ tháng 10 vì bạn mua ngày 02/10/2026. Đến ngày yêu cầu hoàn 12/10/2026 đã qua 10 ngày, trong thời hạn 14 ngày. Sản phẩm chưa kích hoạt nên bạn đủ điều kiện hoàn tiền, không thu phí (0%). Căn cứ: `data/policies/policy-from-oct.md`.

**Bằng chứng cần đối chiếu:** lịch sử có nội dung `SKILL.md` và `references/answer-template.md`; kết quả đọc chính sách thể hiện phạm vi từ `2026-10-01`, thời hạn 14 ngày và không thu phí; câu trả lời cuối đủ các thành phần theo reference.

### 4.3. Trường hợp C — Đổi tên tài liệu, giữ nguyên nội dung

Báo cáo trước mô tả đổi `policy-before-oct.md` thành `old-policy.md`, đổi `policy-from-oct.md` thành `new-policy.md` và ghi nhận kết luận A, B không thay đổi.

| Lần chạy lại | Chính sách cần chọn | Số ngày | Kết luận | Căn cứ nếu dùng tên đổi trên |
| --- | --- | --- | --- | --- |
| A sau đổi tên | Trước tháng 10 | 8 | Không đủ điều kiện | `data/policies/old-policy.md` |
| B sau đổi tên | Từ tháng 10 | 10 | Đủ điều kiện, phí 0% | `data/policies/new-policy.md` |

Phép kiểm tra chỉ chứng minh khả năng tìm tài liệu động khi chạy trong **cuộc trò chuyện mới**, agent lấy tên mới từ `list_files`, đọc file mới và dẫn đúng đường dẫn mới. Trả lời đúng nhưng sử dụng nội dung từ lịch sử cũ chưa đủ để nghiệm thu.

Báo cáo trước chưa cung cấp định danh phiên hội thoại hoặc vị trí trace chứng minh các điều kiện này. Kết quả đổi tên vì vậy được giữ ở mức **đã báo cáo, cần đối chiếu trace**. Không thực hiện đổi tên bất kỳ file nào trong lần biên tập này.

### 4.4. Trường hợp D — Thiếu trạng thái kích hoạt

**Câu hỏi kiểm tra:**

> Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026.

Câu hỏi có hai ngày nhưng thiếu trạng thái kích hoạt. Có thể xác định khoảng cách 10 ngày và phạm vi chính sách mới, song chưa đủ dữ liệu để kết luận được hoàn tiền.

**Phản hồi cần đạt:**

> Sản phẩm của bạn đã được kích hoạt chưa?

Báo cáo trước ghi nhận agent hỏi bổ sung và chưa kết luận, phù hợp yêu cầu. Agent không được tự giả định “chưa kích hoạt”, khẳng định đủ điều kiện hoặc xác nhận phí hoàn cho giao dịch khi còn thiếu dữ liệu.

**Bằng chứng cần đối chiếu:** thông điệp người dùng không có trạng thái kích hoạt; thông điệp agent hỏi đúng thông tin thiếu và chưa kết luận đủ/không đủ điều kiện. Quy tắc hỏi bổ sung cũng áp dụng khi thiếu ngày mua hoặc ngày yêu cầu hoàn.

## 5. Vị trí bằng chứng cần đối chiếu trong trace

Đề bài yêu cầu báo cáo nêu vị trí bằng chứng. Bản trước chưa có tên file trace, số dòng, mã thông điệp hoặc số thứ tự sự kiện thực tế. Bảng dưới xác định nội dung và loại sự kiện cần tìm; không giả lập một trace đã tồn tại.

| Hạng mục | Vị trí sự kiện cần tìm | Nội dung phải chứng minh | Tình trạng định vị |
| --- | --- | --- | --- |
| T1–T4 | Từng cặp tool call/tool result của kiểm tra trực tiếp. | Đầu vào cụ thể; danh sách hợp lệ hoặc lỗi tương ứng. | Chưa có định danh trace. |
| A | Kết quả `list_files`; kết quả đọc chính sách cũ; câu trả lời cuối. | Tìm và đọc đúng tài liệu; 8 ngày; từ chối; dẫn đúng đường dẫn. | Chưa có định danh trace. |
| B | Sự kiện đưa nội dung skill/reference vào lịch sử; kết quả đọc chính sách mới; câu trả lời cuối. | Skill và reference được sử dụng; 10 ngày; chấp nhận hoàn; phí 0%; căn cứ đúng. | Chưa có định danh trace. |
| A sau đổi tên | Đầu phiên mới; kết quả liệt kê và đọc file đổi tên; câu trả lời cuối. | Không dựa vào lịch sử cũ; kết luận A giữ nguyên; đường dẫn mới. | Chưa có định danh trace. |
| B sau đổi tên | Đầu phiên mới; nội dung skill/reference; kết quả tìm và đọc file mới; câu trả lời cuối. | Kết luận B giữ nguyên; không thu phí; dẫn tài liệu mới. | Chưa có định danh trace. |
| D | Thông điệp người dùng và câu hỏi bổ sung của agent. | Thiếu trạng thái kích hoạt; agent hỏi lại, không giả định hoặc kết luận. | Chưa có định danh trace. |

Để hoàn tất bằng chứng nộp bài, mỗi hạng mục cần tên trace thực tế và số thứ tự sự kiện, mã thông điệp hoặc số dòng tương ứng. Các nhãn T1–T4, A–D chỉ là mã đối chiếu của báo cáo, không phải mã sự kiện của hệ thống.

Khi kiểm tra qua giao diện, cần tải lại trang để cập nhật catalog và mở cuộc trò chuyện mới. Câu hỏi chỉ chứa tình huống khách hàng, không nhắc tên skill, tên file hoặc chỉ định thứ tự gọi tool. Không đưa `.env` hay API key vào hồ sơ nộp bài.

## 6. Trả lời câu hỏi cuối bài

### 6.1. Vì sao cần tool tìm file và skill chọn chính sách?

Tool cung cấp khả năng quan sát dữ liệu thực tế: `list_files` cho biết tài liệu hiện có và đường dẫn; `read_file` cung cấp nội dung làm căn cứ. Nhờ đó, tên file có thể thay đổi mà agent vẫn tìm được tài liệu trong thư mục quy định.

Skill cung cấp quy trình sử dụng các khả năng đó: kiểm tra đầu vào, tìm và đọc tài liệu, chọn phiên bản theo ngày mua, tính chênh lệch ngày, kiểm tra kích hoạt và trả lời theo reference. Skill giúp tái sử dụng quy trình và duy trì cấu trúc trả lời nhất quán.

Hai thành phần bổ sung cho nhau. Có tool nhưng thiếu quy trình, agent vẫn có thể chọn nhầm chính sách theo ngày yêu cầu hoàn hoặc bỏ qua thông tin thiếu. Có skill nhưng thiếu khả năng tìm tài liệu, agent không thể tự xác định đường dẫn mới khi tên thay đổi.

### 6.2. Nếu chưa có tool tìm file, sửa prompt có giải quyết yêu cầu đổi tên không?

**Chỉ sửa prompt không giải quyết được yêu cầu tự tìm tài liệu sau đổi tên trong bối cảnh bài tập.** Prompt có thể hướng dẫn cách làm, nhưng không tự cung cấp khả năng liệt kê thư mục hoặc quan sát đường dẫn mới.

Nếu người dùng cập nhật tên mới vào prompt, agent có thể gọi `read_file` với đường dẫn được cung cấp. Tuy nhiên, cách đó phụ thuộc vào việc sửa thủ công sau mỗi lần đổi tên, không đáp ứng yêu cầu tự khám phá tài liệu. Cố định tên file, nội dung chính sách hoặc đáp án trong system prompt còn trái giới hạn của đề bài.

Giải pháp phù hợp là bổ sung và đăng ký tool tìm file, đồng thời dùng skill hướng dẫn đọc nội dung và chọn chính sách. Tên tài liệu được lấy từ kết quả tool; quyết định nghiệp vụ được lấy từ chính sách và dữ liệu khách hàng.

## 7. Kết luận đánh giá Stage 02

Kết quả nghiệp vụ được báo cáo trước phù hợp đề bài: A áp dụng chính sách cũ, 8 ngày và không đủ điều kiện; B áp dụng chính sách mới, 10 ngày và đủ điều kiện với phí 0%; sau đổi tên, kết luận phải giữ nguyên và căn cứ chuyển sang đường dẫn mới; khi thiếu trạng thái kích hoạt, agent phải hỏi bổ sung trước khi kết luận.

Các kết quả kiểm tra tool được báo cáo phù hợp với bốn nhóm đầu vào bắt buộc. Tuy nhiên, **chưa đủ bằng chứng để xác nhận nghiệm thu toàn bộ Stage 02**: còn thiếu định danh và vị trí trace, bằng chứng hội thoại mới sau đổi tên, nội dung skill/reference trong lịch sử và cơ sở xác nhận đầy đủ giới hạn truy cập workspace.

Bài học chính là tách rõ ba trách nhiệm: tool giúp tìm và đọc dữ liệu; skill hướng dẫn xử lý nghiệp vụ; trace chứng minh agent đã thực hiện đúng. Kết luận đúng cần đi kèm tài liệu đúng và bằng chứng có thể đối chiếu.
