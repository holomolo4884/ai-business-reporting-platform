import logging
from io import BytesIO

from weasyprint import HTML

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    """Ошибка при генерации PDF."""


class PDFGenerator:
    """
    Генератор PDF из HTML.

    Использует WeasyPrint для конвертации.
    """

    @staticmethod
    def generate_from_html(html_content: str) -> bytes:
        """
        Генерирует PDF из HTML строки.

        Args:
            html_content: HTML контент для конвертации.

        Returns:
            Байты PDF файла.

        Raises:
            PDFGenerationError: Если генерация не удалась.
        """
        if not html_content:
            raise PDFGenerationError("HTML контент пуст")

        try:
            logger.info("Начало генерации PDF (размер HTML: %d символов)", len(html_content))

            # Создаём PDF в памяти
            pdf_buffer = BytesIO()

            # Конвертируем HTML в PDF
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(pdf_buffer)

            # Получаем байты
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            logger.info("PDF сгенерирован (размер: %d байт)", len(pdf_bytes))

            return pdf_bytes

        except Exception as exc:
            logger.exception("Ошибка при генерации PDF")
            raise PDFGenerationError(f"Не удалось сгенерировать PDF: {exc}") from exc
