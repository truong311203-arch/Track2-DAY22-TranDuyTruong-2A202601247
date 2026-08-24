"""
Bước 4 — Guardrails AI Validators
====================================
NHIỆM VỤ:
  1. Xây dựng PIIDetector: phát hiện & redact email, số điện thoại, SSN, số thẻ tín dụng
  2. Xây dựng JSONFormatter: tự động sửa JSON lỗi
  3. Bọc mỗi validator trong Guard và test với các mẫu đầu vào
  4. Chạy demo với 6 trường hợp PII và 5 trường hợp JSON

DELIVERABLE: Tất cả test cases pass (PII bị redact, JSON được sửa thành công)

CÁC KHÁI NIỆM CHÍNH:
  - @register_validator     — khai báo custom validator class
  - Validator.validate()    — implement logic kiểm tra + sửa
  - OnFailAction.FIX        — thay thế output thay vì raise error
  - Guard().use(validator)  — gắn validator instance vào guard
  - guard.validate(text)    → ValidationOutcome
      .validation_passed    — bool
      .validated_output     — output đã được xử lý

⚠️  QUAN TRỌNG: on_fail phải truyền vào CONSTRUCTOR của VALIDATOR, KHÔNG phải Guard.use()
    SAI  : Guard().use(PIIDetector, on_fail=OnFailAction.FIX)   ← TypeError
    ĐÚNG : Guard().use(PIIDetector(on_fail=OnFailAction.FIX))   ← correct
"""

import re
import json

from guardrails import Guard
from guardrails.validators import Validator, register_validator, PassResult, FailResult

try:
    from guardrails.hub import OnFailAction
except ImportError:
    from guardrails.validator_base import OnFailAction


# ── 1. PII Detector Validator ──────────────────────────────────────────────
@register_validator(name="custom/pii-detector", data_type="string")
class PIIDetector(Validator):
    """
    Phát hiện và redact Personally Identifiable Information (PII).

    Các pattern được phát hiện:
      EMAIL       : xxx@xxx.xxx
      PHONE       : (123) 456-7890 hoặc 123-456-7890
      SSN         : 123-45-6789
      CREDIT_CARD : 1234 5678 9012 3456 (hoặc dấu gạch nối)
    """

    # Regex patterns cho từng loại PII — đã được định nghĩa sẵn, bạn chỉ cần dùng
    PII_PATTERNS = {
        "EMAIL":       r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "PHONE":       r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\b\d{3}\b)[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN":         r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }

    def validate(self, value: str, metadata: dict):
        """
        Tìm PII trong value; nếu phát hiện, redact và trả về FailResult với fix_value.
        """
        redacted_text = value
        found_pii     = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                found_pii.append(pii_type)
                redacted_text = re.sub(pattern, f"[{pii_type}_REDACTED]", redacted_text)

        if found_pii:
            print(f"  ⚠️  Đã redact {len(found_pii)} loại PII: {found_pii}")
            return FailResult(
                error_message=f"Phát hiện PII: {', '.join(found_pii)}",
                fix_value=redacted_text,
            )

        return PassResult()


# ── 2. JSON Formatter Validator ────────────────────────────────────────────
@register_validator(name="custom/json-formatter", data_type="string")
class JSONFormatter(Validator):
    """
    Validate và tự động sửa JSON lỗi.

    Các lỗi có thể sửa tự động:
      - Strip markdown code fences (``` hoặc ```json)
      - Thay single quotes → double quotes
      - Xóa trailing commas trước } hoặc ]
      - Re-serialize với json.dumps để định dạng chuẩn
    """

    @staticmethod
    def _repair(text: str) -> str:
        """
        Cố gắng sửa chuỗi JSON lỗi.

        Bước:
          1. Strip whitespace đầu/cuối
          2. Xóa markdown fences bằng re.sub
          3. Thay single quotes → double quotes
          4. Xóa trailing commas trước } hoặc ]
          5. Trả về chuỗi đã sửa (chưa re-serialize)
        """
        text = text.strip()

        # Xóa markdown fences
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$',          '', text)
        text = text.strip()

        # Thay single quotes → double quotes
        text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
        text = text.replace("'", '"')

        # Xóa trailing commas trước } hoặc ]
        text = re.sub(r',\s*([}\]])', r'\1', text)

        return text

    def validate(self, value: str, metadata: dict):
        """
        Thử parse value thành JSON.
        Nếu thất bại, gọi _repair() rồi thử lại.

        Trả về PassResult nếu JSON hợp lệ ban đầu.
        Trả về FailResult với fix_value là JSON đã sửa nếu sửa thành công.
        Trả về FailResult với fallback JSON nếu JSON không thể sửa được.
        """
        # Thử parse JSON trực tiếp
        try:
            json.loads(value)
            return PassResult()
        except json.JSONDecodeError:
            pass

        # Thử sửa JSON rồi parse lại
        try:
            repaired_text = self._repair(value)
            json.loads(repaired_text)
            print(f"  🔧 JSON đã được sửa thành công")
            return FailResult(
                error_message="JSON đã được sửa tự động",
                fix_value=repaired_text,
            )
        except json.JSONDecodeError as e:
            fallback = json.dumps({
                "error": "Khong the phan tich JSON",
                "raw": value[:200],
            }, ensure_ascii=False)
            return FailResult(
                error_message=f"JSON không hợp lệ sau khi sửa: {e}",
                fix_value=fallback,
            )



# ── 3. Demo: PII Guard ─────────────────────────────────────────────────────
def demo_pii_guard() -> str:
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("\n" + "=" * 55)
    log("  Demo: PII Detection & Redaction")
    log("=" * 55)

    guard = Guard().use(PIIDetector(on_fail=OnFailAction.FIX))

    test_cases = [
        ("Email",        "Contact John at john.doe@example.com for details."),
        ("Phone",        "Call our support line at (555) 867-5309."),
        ("SSN",          "Patient SSN is 123-45-6789 on file."),
        ("Credit Card",  "Payment made with card 4532 1234 5678 9010."),
        ("Multi-PII",    "Email: alice@example.com, Phone: 555-123-4567"),
        ("Clean",        "No sensitive information in this text."),
    ]

    for label, text in test_cases:
        result = guard.validate(text)

        log(f"\n[{label}]")
        log(f"  Input:  {text}")
        log(f"  Output: {result.validated_output}")

    return "\n".join(lines)


# ── 4. Demo: JSON Guard ────────────────────────────────────────────────────
def demo_json_guard() -> str:
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("\n" + "=" * 55)
    log("  Demo: JSON Formatting & Repair")
    log("=" * 55)

    guard = Guard().use(JSONFormatter(on_fail=OnFailAction.FIX))

    test_cases = [
        ("Valid JSON",       '{"name": "Alice", "age": 30}'),
        ("Markdown fences",  '```json\n{"name": "Bob"}\n```'),
        ("Single quotes",    "{'name': 'Charlie', 'score': 95}"),
        ("Trailing comma",   '{"key": "value",}'),
        ("Truly invalid",    "This is not JSON at all: ??? {]"),
    ]

    for label, text in test_cases:
        result = guard.validate(text)

        status = "✅ Pass" if result.validation_passed else "❌ Fail"
        log(f"\n[{label}] {status}")
        log(f"  Input:  {text[:60]}")
        log(f"  Output: {str(result.validated_output)[:60]}")

    return "\n".join(lines)


# ── 5. Main ────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Bước 4: Guardrails AI Validators")
    print("=" * 55)

    from pathlib import Path
    evidence_dir = Path(__file__).parent.parent / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    pii_log = demo_pii_guard()
    (evidence_dir / "04_pii_demo_log.txt").write_text(pii_log, encoding="utf-8")

    json_log = demo_json_guard()
    (evidence_dir / "04_json_demo_log.txt").write_text(json_log, encoding="utf-8")

    print("\n✅ Bước 4 hoàn thành! Đã lưu log vào evidence/04_pii_demo_log.txt và evidence/04_json_demo_log.txt")


if __name__ == "__main__":
    main()


