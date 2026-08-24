# Báo Cáo Thực Nghiệm & Đánh Giá — Day 22: LangSmith + Prompt Versioning

**Học viên:** Trần Duy Trường
**Mã học viên / ID:** 2A202601247  
**Dự án:** Track 2 — Day 22: LangSmith, Prompt Hub, RAGAS & Guardrails AI  
**LangSmith Project URL:** [https://smith.langchain.com/o/bd979d90-0089-419c-96f7-f2d9194ca4e7/projects/p/a4432055-3c9c-481c-b9d8-c697b5fbbf27](https://smith.langchain.com/o/bd979d90-0089-419c-96f7-f2d9194ca4e7/projects/p/a4432055-3c9c-481c-b9d8-c697b5fbbf27)

---

## 1. Danh Mục Tệp Bằng Chứng (Evidence Index)

| Tệp | Mô tả | Trạng thái |
|---|---|---|
| `evidence/01_langsmith_traces.png` | Ảnh chụp màn hình giao diện LangSmith hiển thị ≥ 50 traces cho RAG pipeline cơ sở. | Đã hoàn thành |
| `evidence/02_prompt_hub.png` | Ảnh chụp màn hình Prompt Hub trên LangSmith hiển thị 2 phiên bản prompt đã được push. | Đã hoàn thành |
| `evidence/02_ab_routing_log.txt` | Toàn bộ console log định tuyến A/B tất định (MD5 hash) cho 50 câu truy vấn kèm nhãn phiên bản `[prompt-v1]` / `[prompt-v2]`. | Đã hoàn thành |
| `evidence/03_ragas_scores.png` | Ảnh chụp màn hình terminal hiển thị bảng so sánh 4 chỉ số RAGAS giữa V1 và V2. | Đã hoàn thành |
| `evidence/03_ragas_report.json` | Báo cáo chi tiết định dạng JSON lưu trữ điểm số 4 chỉ số RAGAS của cả 2 phiên bản prompt. | Đã hoàn thành |
| `evidence/04_pii_demo_log.txt` | Output console kiểm thử bộ lọc PII Validator với 6 test cases (Email, Phone, SSN, Credit Card, Multi-PII, Clean). | Đã hoàn thành |
| `evidence/04_json_demo_log.txt` | Output console kiểm thử bộ sửa lỗi JSON Formatter với 5 test cases (Valid, Markdown fences, Single quotes, Trailing comma, Irreparable). | Đã hoàn thành |

---

## 2. Phân Tích Định Lượng & So Sánh: Prompt V1 vs Prompt V2

### 2.1. Bảng Điểm Đánh Giá RAGAS Thực Nghiệm

| Chỉ số (Metric) | Prompt V1 (Ngắn gọn) | Prompt V2 (Có cấu trúc) | Phiên bản thắng (Winner) | Mục tiêu / Chuẩn |
|---|:---:|:---:|:---:|:---:|
| **Faithfulness** | **0.9310** | **0.8756** | **← V1** | $\ge 0.80$ (Đạt mục tiêu + Điểm thưởng V1 $\ge 0.90$) |
| **Answer Relevancy** | **0.9163** | **0.8850** | **← V1** | Rất cao |
| **Context Recall** | **1.0000** | **1.0000** | **Hòa (100%)** | Tuyệt đối (1.0) |
| **Context Precision** | **0.9417** | **0.9383** | **← V1** | Rất cao |

---

### 2.2. Phân Tích Chuyên Sâu Kết Quả Thực Nghiệm

1. **Faithfulness (0.9310 ở V1 so với 0.8756 ở V2):**
   - **Vì sao V1 đạt điểm Faithfulness cao hơn (0.9310 $\ge 0.90$)?**
     - Prompt V1 yêu cầu trả lời trực tiếp trong 2–4 câu và bám sát context mà không đưa thêm các cấu trúc dẫn dắt. Khi RAGAS trích xuất các claims (mệnh đề khẳng định) từ câu trả lời của V1, hầu hết 100% các câu đều là phát biểu trực tiếp trích từ context của FAISS, do đó tỷ lệ claims được chứng thực (grounded) đạt mức xuất sắc 93.10%.
     - Prompt V2 yêu cầu chia thành 3 phần rõ rệt ("1) Luận điểm chính, 2) Trích dẫn facts, 3) Kết luận"). Đôi khi mô hình bổ sung thêm các câu liên kết hoặc tóm tắt khái quát để tạo cấu trúc luận điểm, khiến RAGAS phân tích thành các claim phụ không hoàn toàn xuất hiện nguyên văn trong đoạn context truy xuất, dẫn đến điểm trung thực hơi thấp hơn một chút (87.56% nhưng vẫn vượt xa ngưỡng chuẩn 80%).

2. **Answer Relevancy (0.9163 ở V1 so với 0.8850 ở V2):**
   - Prompt V1 trả lời ngắn gọn và đi thẳng vào trọng tâm câu hỏi của người dùng. Khi RAGAS sinh các câu hỏi giả định (synthetic questions) từ câu trả lời ngắn gọn của V1, độ tương đồng embedding với câu hỏi gốc đạt 91.63%.
   - Prompt V2 do có cấu trúc luận điểm chi tiết nên câu hỏi giả định sinh ra bao hàm nhiều khía cạnh phân tích hơn, làm độ tương đồng tập trung với câu hỏi gốc là 88.50%.

3. **Context Recall (1.0000 / 100% ở cả 2 phiên bản):**
   - Cả 2 phiên bản đều đạt điểm tuyệt đối 1.0000 (100%). Điều này chứng minh thuật toán chia chunk `RecursiveCharacterTextSplitter` với `chunk_size=500` và `chunk_overlap=50`, kết hợp với FAISS retriever lấy `top_k=3` đã bao phủ 100% các sự kiện cần thiết để trả lời chính xác đối chiếu với Ground Truth reference answers (`QA_PAIRS`).

4. **Context Precision (0.9417 ở V1 và 0.9383 ở V2):**
   - Độ chính xác vị trí ngữ cảnh đạt trên 94%, khẳng định FAISS đã xếp hạng các đoạn văn có độ liên quan cao nhất ở ngay vị trí đầu tiên (rank 1), tối ưu hóa luồng đọc của LLM.

---

## 3. Kết Quả Kiểm Thử Guardrails AI

### 3.1. PII Detector (`PIIDetector`)
- Triển khai thành công validator tùy chỉnh bằng decorator `@register_validator` và cơ chế tự động sửa lỗi `on_fail=OnFailAction.FIX`.
- Nhận diện chính xác 4 mẫu biểu thức chính quy (Regex):
  - **EMAIL**: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b` $\rightarrow$ `[EMAIL_REDACTED]`
  - **PHONE**: `(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\b\d{3}\b)[-.\s]?\d{3}[-.\s]?\d{4}\b` $\rightarrow$ `[PHONE_REDACTED]`
  - **SSN**: `\b\d{3}-\d{2}-\d{4}\b` $\rightarrow$ `[SSN_REDACTED]`
  - **CREDIT_CARD**: `\b(?:\d{4}[-\s]?){3}\d{4}\b` $\rightarrow$ `[CREDIT_CARD_REDACTED]`
- Đã kiểm thử trên 6 trường hợp: phát hiện và che toàn bộ dữ liệu nhạy cảm đơn lẻ cũng như đa PII trong cùng văn bản, giữ nguyên 100% văn bản an toàn (Clean text).

### 3.2. JSON Formatter (`JSONFormatter`)
- Tự động sửa chữa các lỗi phổ biến từ đầu ra của LLM:
  1. Gỡ bỏ Markdown code fences (````json ... ```` hoặc ````...````).
  2. Chuẩn hóa nháy đơn `'` thành nháy kép `"` chuẩn JSON.
  3. Xóa dấu phẩy thừa (trailing commas) trước dấu đóng ngoặc `}` hoặc `]`.
  4. Trả về JSON lỗi dự phòng chuẩn `{"error": "Khong the phan tich JSON", "raw": "..."}` khi chuỗi hoàn toàn không thể phục hồi.
- Đã kiểm thử trên 5 trường hợp và vượt qua 100%.

---

## 4. Hướng Dẫn Tái Hiện Kết Quả (Reproduction)

```bash
# Chạy toàn bộ pipeline tự động từ đầu đến cuối
python src/run_all.py

# Hoặc chạy từng bước độc lập:
python src/01_langsmith_rag_pipeline.py  # Bước 1: RAG + LangSmith Tracing
python src/02_prompt_hub_ab_routing.py   # Bước 2: Prompt Hub & A/B Routing
python src/03_ragas_evaluation.py        # Bước 3: RAGAS Evaluation
python src/04_guardrails_validator.py    # Bước 4: Guardrails AI Validators
```
