# LAB DAY 19: XÂY DỰNG HỆ THỐNG GRAPHRAG VỚI TECH COMPANY CORPUS

## 1. MỤC TIÊU BÀI HỌC

- Hiểu rõ quy trình trích xuất thực thể (Entity Extraction) và quan hệ (Relation Extraction) từ văn bản thô.
- Làm quen với các thư viện quản lý đồ thị: NetworkX, Neo4j và framework mã nguồn mở NodeRAG.
- Xây dựng hoàn chỉnh một pipeline GraphRAG: từ lập chỉ mục (Indexing) đến truy vấn đa bước (Multi-hop Querying).
- Đánh giá sự khác biệt về độ chính xác giữa Flat RAG và GraphRAG.

---

## 2. PHẦN 1: NGHIÊN CỨU VÀ CHUẨN BỊ (RESEARCH)

### 2.1. Quy trình xử lý dữ liệu đồ thị

Sinh viên cần trả lời các câu hỏi sau:

1. **Entity Extraction**: Làm sao để LLM phân biệt được đâu là thực thể (Node) và đâu là thuộc tính?
2. **Graph Construction**: Tại sao việc khử trùng lặp (Deduplication) lại quan trọng trong đồ thị?
3. **Query Answering**: Sự khác biệt giữa duyệt đồ thị theo chiều rộng (BFS) và tìm kiếm vector thông thường là gì?

### 2.2. Tìm hiểu công cụ

- **NetworkX**: Thư viện Python dùng để nghiên cứu các mạng lưới phức tạp. Phù hợp cho việc tạo prototype nhanh.
- **Neo4j**: Cơ sở dữ liệu đồ thị chuẩn công nghiệp, sử dụng ngôn ngữ truy vấn Cypher.
- **NodeRAG**: Framework mã nguồn mở xây dựng trên nền NetworkX, giúp đơn giản hóa việc tích hợp GraphRAG vào ứng dụng Python.

---

## 3. PHẦN 2: ENVIRONMENT SETUP

Mở terminal hoặc command prompt và cài đặt các thư viện cần thiết:

```bash
# Cài đặt các thư viện cơ bản cho xử lý ngôn ngữ và đồ thị
pip install networkx matplotlib neo4j openai pandas

# Cài đặt NodeRAG framework
pip install noderag

# Nếu sử dụng LangChain để hỗ trợ pipeline
pip install langchain langchain-openai
```

> **Lưu ý**:
>
> - Đối với Neo4j, nên sử dụng Neo4j Desktop hoặc chạy qua Docker để có giao diện trực quan hóa (Neo4j Browser / Bloom).

---

## 4. PHẦN 3: HƯỚNG DẪN THỰC HIỆN TỪNG BƯỚC

### Bước 1: Trích xuất thực thể và quan hệ (Indexing)

Sử dụng LLM để đọc bộ dữ liệu _Tech Company Corpus_ và chuyển đổi thành các bộ ba (Triples).

**Ví dụ:**

- Input:

  > "OpenAI được thành lập bởi Sam Altman và Elon Musk vào năm 2015."

- Output (Triples):
  - (OpenAI, FOUNDED_BY, Sam Altman)
  - (OpenAI, FOUNDED_BY, Elon Musk)
  - (OpenAI, FOUNDED_IN, 2015)

---

### Bước 2: Xây dựng đồ thị (Construction)

Sinh viên lựa chọn một trong các công cụ sau:

- **Lựa chọn A - NetworkX**: Phù hợp để chạy offline trong Notebook.
- **Lựa chọn B - Neo4j**: Khuyên dùng nếu muốn trực quan hóa các mối liên kết.
- **Lựa chọn C - NodeRAG**: Giải pháp all-in-one đã tối ưu sẵn logic tìm kiếm.

---

### Bước 3: Thực thi truy vấn (Querying)

Thiết kế pipeline truy vấn theo các bước:

1. Nhận câu hỏi từ người dùng.
2. Trích xuất thực thể chính trong câu hỏi (ví dụ: "Google").
3. Tìm node tương ứng trong đồ thị.
4. Duyệt các node lân cận trong phạm vi **2-hop**.
5. Gộp thông tin (Textualization) và gửi cho LLM để sinh câu trả lời.

---

### Bước 4: So sánh và Đánh giá (Evaluation)

Thực hiện so sánh giữa hai hệ thống:

1. **Flat RAG**: Sử dụng ChromaDB hoặc FAISS.
2. **GraphRAG**: Sử dụng đồ thị tri thức.

**Yêu cầu:**

- Chạy thử ít nhất 5 câu hỏi phức tạp.
- Ghi nhận các trường hợp:
  - Flat RAG bị hallucination.
  - GraphRAG trả lời chính xác.

---

## 5. ĐỀ XUẤT CÔNG CỤ (RECOMMENDATIONS)

| Mục tiêu              | Tool gợi ý | Lý do                                                             |
| --------------------- | ---------- | ----------------------------------------------------------------- |
| Dễ bắt đầu            | NodeRAG    | Tích hợp sẵn logic GraphRAG, không cần cấu hình database phức tạp |
| Trực quan hóa tốt     | Neo4j      | Giao diện đồ họa giúp thấy rõ mối quan hệ tri thức                |
| Nghiên cứu thuật toán | NetworkX   | Cho phép can thiệp sâu vào thuật toán đồ thị                      |

---

## 6. DELIVERABLES

Sinh viên cần nộp:

1. **Mã nguồn** (.py hoặc .ipynb)
2. **Ảnh chụp đồ thị tri thức** (Neo4j hoặc Matplotlib)
3. **Bảng so sánh 20 câu hỏi benchmark** giữa Flat RAG và GraphRAG
4. **Phân tích chi phí**:
   - Token usage
   - Thời gian xử lý

---

## 7. GỢI Ý MỞ RỘNG (OPTIONAL)

- Áp dụng multi-hop reasoning phức tạp (>2-hop)
- Kết hợp GraphRAG với Agent (LangGraph / ReAct)
- Tối ưu hóa truy vấn bằng hybrid search (Graph + Vector)
- Thử nghiệm với dataset lớn hơn (Wikipedia, Papers, GitHub repos)

---

## 8. KẾT LUẬN

Bài lab giúp sinh viên hiểu sâu về:

- Sự khác biệt giữa truy xuất dựa trên vector và đồ thị
- Cách tổ chức tri thức có cấu trúc
- Ứng dụng GraphRAG trong các hệ thống AI thực tế

GraphRAG là một hướng tiếp cận mạnh mẽ giúp giảm hallucination và tăng khả năng suy luận đa bước của LLM.
