import pytest

from reports.pdf_generator import PDFGenerationError, PDFGenerator


class TestPDFGenerator:
    """Тесты PDFGenerator."""

    def test_generate_simple_pdf(self):
        """Генерация простого PDF."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Test</title></head>
        <body><h1>Тестовый отчёт</h1><p>Привет, мир!</p></body>
        </html>
        """

        pdf_bytes = PDFGenerator.generate_from_html(html)

        # PDF должен быть не пустым
        assert len(pdf_bytes) > 0

        # PDF должен начинаться с сигнатуры %PDF-
        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_pdf_with_cyrillic(self):
        """Генерация PDF с кириллицей."""
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head><meta charset="UTF-8"><title>Отчёт</title></head>
        <body>
            <h1>Отчёт о продажах</h1>
            <p>Организация: Тестовая компания</p>
            <p>Выручка: 100,000 рублей</p>
            <p>Расходы: 50,000 рублей</p>
        </body>
        </html>
        """

        pdf_bytes = PDFGenerator.generate_from_html(html)

        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_pdf_with_empty_html_raises_error(self):
        """Пустой HTML вызывает ошибку."""
        with pytest.raises(PDFGenerationError) as exc_info:
            PDFGenerator.generate_from_html("")

        assert "пуст" in str(exc_info.value)

    def test_generate_pdf_with_invalid_html(self):
        """Невалидный HTML может быть обработан WeasyPrint."""
        html = "<h1>Тест</h1><p>Без закрывающих тегов"

        # WeasyPrint обычно справляется с невалидным HTML
        pdf_bytes = PDFGenerator.generate_from_html(html)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_styles(self):
        """Генерация PDF с CSS стилями."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; color: #333; }
                h1 { color: blue; }
                .card { border: 1px solid #ccc; padding: 10px; }
            </style>
        </head>
        <body>
            <h1>Заголовок</h1>
            <div class="card">Карточка с текстом</div>
        </body>
        </html>
        """

        pdf_bytes = PDFGenerator.generate_from_html(html)
        assert len(pdf_bytes) > 0
