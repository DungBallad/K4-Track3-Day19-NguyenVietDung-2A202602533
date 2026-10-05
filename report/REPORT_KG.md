# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Nguyễn Viết Dũng  **MSSV:** 2A202602533  **Ngày:** 05/10/2026

> Kỳ vọng và thang điểm: `SUBMISSION.md`. Mọi số liệu phải khớp với `ket_qua_benchmark_kg.txt`. Bản thiết kế ontology nộp riêng ở `report/ONTOLOGY.md`.

## 1. Chi phí (10 điểm)

Dán 2 bảng `Indexing` và `Querying` từ `ket_qua_benchmark_kg.txt`:

```
== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176     56072        0   0.00112    102.6
graph       196     91958     4648   0.00929    182.8

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.43   1.00      694       47   0.00013     3.01
graph       0.74   1.50     3323       70   0.00053     3.71
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | $0.00112 | $0.00929 | ×8.30 |
| Indexing giây | 102.6s | 182.8s | ×1.78 |
| Mỗi câu: USD | $0.00013 | $0.00053 | ×4.08 |
| Mỗi câu: giây | 3.01s | 3.71s | ×1.23 |
| Mỗi câu: in_tok | 694 | 3323 | ×4.79 |

**Chi phí tăng thêm đến từ đâu?** (2–3 câu)
> Ở giai đoạn **Indexing**, chi phí tăng gấp ~8.3 lần chủ yếu do bước trích xuất thực thể và quan hệ từ 20 bài báo tin tức bằng LLM (`extract_news_cases` với JSON mode sinh thêm 4,648 output tokens và hơn 35k input tokens), trong khi Flat RAG chỉ tốn chi phí embedding thuần túy. Ở giai đoạn **Querying**, chi phí mỗi câu hỏi tăng gấp ~4.08 lần vì đồ thị mở rộng multi-hop nạp thêm danh sách dữ kiện có cấu trúc (`facts`) vào prompt, làm số lượng `in_tok` trung bình tăng gấp ~4.79 lần (3,323 tokens so với 694 tokens của Flat RAG). Tuy nhiên, độ trễ thời gian phản hồi mỗi câu chỉ tăng nhẹ 23% (3.71s so với 3.01s), hoàn toàn nằm trong ngưỡng chấp nhận được của hệ thống sản xuất.

---

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1.00 / 2 | 1.00 / 2 | Hòa | Cả hai pipeline đều trích xuất trọn vẹn định nghĩa tiền chất từ văn bản Điều 2 Luật Phòng, chống ma túy 2021 nằm gọn trong một chunk. |
| Q2 | single-hop-news | 1.00 / 2 | 1.00 / 2 | Hòa | Thông tin hai bị cáo lãnh án tử hình (Trần Thanh Tuấn, Trần Minh Tâm) nằm tập trung trong một bài báo nên vector search của Flat RAG đã đủ để trả lời chính xác. |
| Q3 | cross-kb | 0.00 / 0 | 1.00 / 2 | Graph | Flat RAG hoàn toàn chịu thua ("Không đủ thông tin") vì dữ kiện vụ án ở tin tức còn khung hình phạt ở luật; GraphRAG kết nối thành công qua node cầu nối Crime sang Điều 251 khoản 1. |
| Q4 | cross-kb | 0.00 / 0 | 0.00 / 0 | Hòa | Flat RAG thiếu liên kết giữa 2 KB, còn GraphRAG dù truy xuất đủ 5 khoản Điều 255 nhưng LLM quá thận trọng trước câu hỏi suy luận mức phạt tối đa của một đối tượng chưa bị tuyên án. |
| Q5 | cross-kb-multi-hop | 0.60 / 1 | 0.80 / 1 | Graph | GraphRAG vượt trội về recall (0.80 vs 0.60) khi đối chiếu thành công khối lượng 9,6kg MDMA với khung hình phạt tại khoản 4 (20 năm, chung thân hoặc tử hình). |
| Q6 | aggregation | 0.00 / 1 | 0.67 / 2 | Graph | Flat RAG chỉ tìm được chunk vụn vặt và không nêu được tên đối tượng chính; GraphRAG duyệt qua các cạnh INVOLVES quanh node MDMA để tổng hợp đầy đủ 3 vụ án lớn (Cái Quang Huy, Lê Minh Thành, Sầm Sơn). |

---

## 3. Phân tích lỗi (20 điểm)

### Lỗi E5: LLM lệch với graph (Hallucination Điều luật ở câu Q5)

- **Hiện tượng:** Ở câu hỏi Q5 về vụ án Cái Quang Huy, Knowledge Graph đã liên kết chính xác hành vi của Huy với tội danh và Điều luật tương ứng trong BLHS. Tuy nhiên, trong câu trả lời tổng hợp, LLM lại khẳng định áp dụng *"khoản 4 của Điều 251 Bộ luật Hình sự"* thay vì *"Điều 250 Bộ luật Hình sự"* (Tội vận chuyển trái phép chất ma túy).
- **Bằng chứng:**
  * Trích câu trả lời của GraphRAG trong `ket_qua_benchmark_kg.txt` (Q5):
    > *"Cái Quang Huy bị truy tố về tội 'vận chuyển trái phép chất ma túy' với loại ma túy là MDMA. Với khối lượng MDMA trong vụ này là hơn 9,6kg, khoản áp dụng tương ứng là khoản 4 của Điều 251 Bộ luật Hình sự (BLHS). Khung hình phạt theo khoản này là từ 20 năm tù, tù chung thân hoặc tử hình."*
  * Truy vấn Cypher kiểm tra trực tiếp đồ thị:
  ```cypher
  MATCH (p:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(c:Crime)<-[:DEFINES]-(a:Article)
  RETURN p.name AS person, c.name AS crime, a.id AS article, a.title AS title;
  ```
  * Kết quả trả về từ Neo4j:
  ```
  person: "Cái Quang Huy"
  crime: "vận chuyển trái phép chất ma túy"
  article: "Điều 250 BLHS"
  title: "Tội vận chuyển trái phép chất ma túy"
  ```
- **Nguyên nhân:** Đồ thị lưu trữ và cung cấp hoàn toàn đúng `Điều 250 BLHS`. Tuy nhiên, do trong prompt có nhiều dữ kiện xuất hiện từ ngữ *"Điều 251 BLHS"* (vốn là tội danh phổ biến nhất trong các bài báo khác như vụ Lê Minh Thành) và cấu trúc mức phạt tại khoản 4 của Điều 250 và Điều 251 rất tương đồng ("tù 20 năm, tù chung thân hoặc tử hình"), LLM `gpt-4o-mini` đã bị thiên kiến ngữ cảnh (context bias) dẫn đến việc trích dẫn nhầm mã Điều luật 251 thay cho 250.
- **Đề xuất sửa:** 
  1. Thêm chỉ dẫn nghiêm ngặt trong `GRAPH_PROMPT`: *"BẮT BUỘC trích dẫn chính xác mã Điều luật đi kèm trực tiếp với tội danh của vụ án trong dữ kiện Knowledge Graph; không được tự suy đoán hoặc thay thế mã Điều luật khác."*
  2. Bổ sung trích xuất có cấu trúc (Structured Outputs): Yêu cầu LLM trả về JSON gồm các trường `article_id`, `clause_number`, `penalty` thay vì sinh tự do dạng văn xuôi. Đánh đổi: tốn thêm khoảng 10-15% output token nhưng loại bỏ hoàn toàn hiện tượng lệch số hiệu điều luật.

---

### Lỗi E1: Cầu nối gãy & LLM bị quá thận trọng trước câu hỏi suy luận suy diễn (Câu Q4)

- **Hiện tượng:** Ở câu Q4 (*"Giang hồ 'Hoàng Nato' bị bắt về hành vi gì, và hành vi đó có thể bị phạt tù tối đa bao nhiêu theo Bộ luật Hình sự?"*), cả Flat RAG và GraphRAG đều trả về kết quả rỗng: `"Không đủ thông tin."` (recall = 0.00, judge = 0).
- **Bằng chứng:**
  * Trích câu trả lời Q4 trong `ket_qua_benchmark_kg.txt`:
    > `--- Q4 [cross-kb] graph recall=0.00 judge=0 2.75s`  
    > `Không đủ thông tin.`
  * Kiểm tra thực tế trong đồ thị Neo4j bằng Cypher:
  ```cypher
  MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(c:Crime)<-[:DEFINES]-(a:Article)-[:HAS_CLAUSE]->(cl:Clause)
  WHERE 'Hoàng Nato' IN p.aliases OR p.name = 'Dương Minh Tuấn'
  RETURN p.name, p.aliases, r.charge, c.name, a.id, collect(cl.number) AS clauses;
  ```
  * Kết quả trả về:
  ```
  p.name: "Dương Minh Tuấn"
  p.aliases: ["Hoàng Nato"]
  r.charge: "tổ chức sử dụng trái phép chất ma túy"
  c.name: "tổ chức sử dụng trái phép chất ma túy"
  a.id: "Điều 255 BLHS"
  clauses: [1, 2, 3, 4, 5]
  ```
- **Nguyên nhân:** 
  1. Graph có đầy đủ node `Person` mang alias `Hoàng Nato`, kết nối đến `Case`, `Crime` và toàn bộ 5 khoản của `Điều 255 BLHS` (trong đó khoản 4 quy định mức phạt cao nhất: tù 20 năm hoặc tù chung thân).
  2. Tuy nhiên, trong bài báo tin tức, đối tượng Dương Minh Tuấn mới chỉ bị bắt giữ/khởi tố điều tra ban đầu, thuộc tính `sentence` trên quan hệ `INVOLVED_IN` bị rỗng (chưa có bản án tuyên phạt cụ thể).
  3. Khi nhận câu hỏi hỏi mức phạt *tối đa*, kết hợp với câu lệnh nhắc nhở trong system prompt *"Nếu ngữ cảnh không đủ, nói không đủ thông tin"*, mô hình LLM hiểu nhầm rằng ngữ cảnh thiếu thông tin phán quyết tòa án đối với Hoàng Nato nên từ chối trả lời, thay vì suy luận khung phạt tối đa theo quy định của Điều 255 BLHS.
- **Đề xuất sửa:**
  1. Tinh chỉnh prompt tại `GRAPH_PROMPT`: Thêm hướng dẫn *"Đối với câu hỏi về khung hình phạt hoặc mức phạt tối đa theo quy định pháp luật của một hành vi, hãy căn cứ vào khung hình phạt cao nhất được quy định tại Điều luật tương ứng trong dữ kiện graph, kể cả khi đối tượng chưa có mức án tuyên cụ thể."*
  2. Bổ sung thuộc tính `max_penalty` trên node `Article` hoặc `Crime` để truy vấn graph có thể trả về trực tiếp thông tin khung phạt cao nhất mà không cần LLM phải tự dò tìm qua 5 khoản.

---

## 4. Kết luận (5 điểm)

Khi nào nên dùng KG, khi nào Flat RAG là đủ? Dẫn số liệu ở mục 1–2:

1. **Khi nào Flat RAG là đủ:**
   * Đối với các câu hỏi tìm kiếm thông tin cục bộ (**Single-hop**), nơi câu trả lời nằm trọn vẹn trong một đoạn văn bản hoặc một tài liệu duy nhất (như câu Q1 và Q2).
   * Cả Flat RAG và GraphRAG đều đạt điểm tuyệt đối (`recall = 1.00`, `judge = 2`). Trong kịch bản này, Flat RAG tối ưu hơn vượt trội: chi phí indexing rẻ hơn 8.3 lần ($0.00112 vs $0.00929) và chi phí mỗi câu hỏi rẻ hơn 4 lần ($0.00013 vs $0.00053) mà không cần duy trì hạ tầng cơ sở dữ liệu đồ thị phức tạp như Neo4j.

2. **Khi nào bắt buộc phải dùng Knowledge Graph (GraphRAG):**
   * Đối với các bài toán truy xuất đa nguồn (**Cross-KB** và **Multi-hop**): Khi thông tin đối tượng nằm ở nguồn A (bài báo tin tức) nhưng căn cứ xử lý pháp lý, khung định lượng nằm ở nguồn B (văn bản luật). Flat RAG thất bại hoàn toàn ở Q3 (`recall = 0.00`), trong khi GraphRAG giải quyết trọn vẹn (`recall = 1.00`, `judge = 2`).
   * Đối với các câu hỏi tổng hợp (**Aggregation**): Như câu Q6 gom nhóm toàn bộ các vụ việc liên quan đến chất ma túy MDMA, GraphRAG đạt `recall = 0.67` (so với `0.00` của Flat RAG) nhờ khả năng duyệt trực tiếp các cạnh quan hệ đồ thị thay vì phụ thuộc vào độ tương đồng vector ngữ nghĩa vốn bị phân tán.

---

## 5. Tự kiểm (5 điểm)

```
$ pytest tests/ -q
................................................                         [100%]
48 passed in 0.29s

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = openrouter:openai/gpt-4o-mini | embedding = openrouter:openai/text-embedding-3-small
[OK] KG-2 build_graph: 146 node / 289 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 13 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00064. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

Ảnh Neo4j: `report/img/kg_count.png`, `report/img/kg_cross_kb.png`, `report/img/kg_my_case.png`.
Người đã chọn cho `kg_my_case.png`: **Cái Quang Huy** (vụ án vận chuyển ma túy MDMA & Ketamine qua sân bay Nội Bài).

---

## Vấn đề gặp phải (không tính điểm)

Lỗi chưa giải quyết được: lệnh đã chạy, toàn bộ thông báo lỗi, những gì đã thử:
> Trong quá trình benchmark trên Windows PowerShell, khi chạy lệnh `python bench_kg.py`, hệ thống ban đầu gặp lỗi mã hóa ký tự `UnicodeEncodeError: 'charmap'` do bảng mã mặc định `cp1258` của Windows không hiển thị được ký tự tiếng Việt UTF-8. Đã khắc phục triệt để bằng cách thiết lập biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi. Ngoài ra, script tự động chụp màn hình Playwright đã được cấu hình xử lý nút Dismiss các pop-up tour của Neo4j Browser để đảm bảo ảnh chụp không bị che khuất thanh truy vấn Cypher và bảng Results Overview.
