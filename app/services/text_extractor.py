import os
import asyncio
from typing import Optional
from app.schemas.contract.file_upload import FileType
import mimetypes

# PDF 처리
try:
    import pypdf
except ImportError:
    pypdf = None

# DOCX 처리
try:
    import docx2txt
except ImportError:
    docx2txt = None

# 이미지 OCR 처리
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

# 텍스트 파일 처리
try:
    import chardet
except ImportError:
    chardet = None


class TextExtractor:
    def __init__(self):
        self.supported_types = {
            FileType.PDF: pypdf is not None,
            FileType.DOCX: docx2txt is not None,
            FileType.TXT: True,
            FileType.IMAGE: pytesseract is not None and Image is not None,
        }

    async def extract_text(self, file_path: str, file_type: FileType) -> Optional[str]:
        """파일에서 텍스트를 추출합니다."""
        try:
            if file_type == FileType.PDF:
                return await self._extract_from_pdf(file_path)
            elif file_type == FileType.DOCX:
                return await self._extract_from_docx(file_path)
            elif file_type == FileType.TXT:
                return await self._extract_from_txt(file_path)
            elif file_type == FileType.IMAGE:
                return await self._extract_from_image(file_path)
            else:
                return None
        except Exception as e:
            print(f"텍스트 추출 실패 ({file_type}): {str(e)}")
            return None

    async def _extract_from_pdf(self, file_path: str) -> Optional[str]:
        """PDF에서 텍스트를 추출합니다."""
        if not pypdf:
            return "PDF 처리 라이브러리가 설치되지 않았습니다."
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"PDF 텍스트 추출 실패: {str(e)}"

    async def _extract_from_docx(self, file_path: str) -> Optional[str]:
        """DOCX에서 텍스트를 추출합니다."""
        if not docx2txt:
            return "DOCX 처리 라이브러리가 설치되지 않았습니다."
        
        try:
            text = docx2txt.process(file_path)
            return text.strip()
        except Exception as e:
            return f"DOCX 텍스트 추출 실패: {str(e)}"

    async def _extract_from_txt(self, file_path: str) -> Optional[str]:
        """TXT 파일에서 텍스트를 추출합니다."""
        try:
            # 인코딩 감지
            if chardet:
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
            else:
                encoding = 'utf-8'
            
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
            return text.strip()
        except Exception as e:
            return f"TXT 텍스트 추출 실패: {str(e)}"

    async def _extract_from_image(self, file_path: str) -> Optional[str]:
        """이미지에서 OCR로 텍스트를 추출합니다."""
        if not pytesseract or not Image:
            return "OCR 라이브러리가 설치되지 않았습니다."
        
        try:
            # 이미지 열기
            image = Image.open(file_path)
            
            # OCR로 텍스트 추출
            text = pytesseract.image_to_string(image, lang='kor+eng')
            return text.strip()
        except Exception as e:
            return f"이미지 OCR 실패: {str(e)}"

    def is_supported(self, file_type: FileType) -> bool:
        """파일 타입이 지원되는지 확인합니다."""
        return self.supported_types.get(file_type, False)


# 전역 인스턴스
text_extractor = TextExtractor()
