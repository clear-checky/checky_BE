import os
import asyncio
from typing import Optional
from app.schemas.upload.file_upload import FileType
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
    import easyocr
    import pillow_heif
    pillow_heif.register_heif_opener()  # HEIF 지원 활성화
except ImportError:
    Image = None
    easyocr = None

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
            FileType.IMAGE: easyocr is not None,
        }
        
        # EasyOCR 리더 초기화
        self.easyocr_reader = None
        if easyocr is not None:
            try:
                self.easyocr_reader = easyocr.Reader(['ko', 'en'])
            except Exception as e:
                print(f"EasyOCR 초기화 실패: {str(e)}")
                self.easyocr_reader = None

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
        # EasyOCR 사용
        if self.easyocr_reader is not None:
            try:
                # 이미지 전처리
                image = Image.open(file_path)
                
                # 이미지 크기 조정 (OCR 성능 향상)
                if image.width > 2000 or image.height > 2000:
                    image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                
                # 회색조 변환 (OCR 정확도 향상)
                if image.mode != 'L':
                    image = image.convert('L')
                
                # 전처리된 이미지 저장
                processed_path = file_path.replace('.', '_processed.')
                image.save(processed_path)
                
                # EasyOCR로 텍스트 추출
                results = self.easyocr_reader.readtext(processed_path)
                text = ' '.join([result[1] for result in results])
                
                # 임시 파일 삭제
                if os.path.exists(processed_path):
                    os.remove(processed_path)
                
                return text.strip()
            except Exception as e:
                return f"EasyOCR 실패: {str(e)}"
        
        return "EasyOCR이 설치되지 않았습니다."

    def is_supported(self, file_type: FileType) -> bool:
        """파일 타입이 지원되는지 확인합니다."""
        return self.supported_types.get(file_type, False)


# 전역 인스턴스
text_extractor = TextExtractor()
