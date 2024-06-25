---
icon: material/star
---

## 🏆 __Best Practices__

- Review Platform Dependencies: Before adding any dependency, ensure it aligns with the Platform's existing dependencies.
- Use Loose Versioning: If possible, specify a range to maintain compatibility. E.g., `>=1.4,<1.5`.
- Testing: Test your extension with the Platform's core to avoid conflicts. Both unit and integration tests are recommended.
- Document Dependencies: Use `pyproject.toml` and `poetry.lock` for clear, up-to-date records

