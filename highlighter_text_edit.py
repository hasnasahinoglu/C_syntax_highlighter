
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QColor
from gui_integration import *


class CustomSyntaxTextEditor(QTextEdit):

    analysisCompleted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Real-time analyzer
        self.analyzer = RealTimeAnalyzer()

        # Highlighting delay timer (performans için)
        self.highlight_timer = QTimer()
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(self.apply_syntax_highlighting)

        # Font ayarları
        font = QFont("Courier New", 11)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab genişliği
        self.setTabStopDistance(40)

        # Event'leri bağla
        self.textChanged.connect(self.on_text_changed)

        # Highlighting durumu
        self.is_highlighting = False
        self.last_highlighted_text = ""

    def on_text_changed(self):
        if not self.is_highlighting:
            # 100ms delay ile highlighting uygula (performans için)
            self.highlight_timer.start(100)

    def apply_syntax_highlighting(self):
        current_text = self.toPlainText()

        # Metin değişmemişse highlighting yapma
        if current_text == self.last_highlighted_text:
            return

        if not current_text.strip():
            return

        # Cursor pozisyonunu kaydet
        cursor = self.textCursor()
        cursor_position = cursor.position()

        # Highlighting işaretçisi
        self.is_highlighting = True

        try:
            # Analizi gerçekleştir
            result = self.analyzer.perform_analysis(current_text)

            if result['success']:
                # Tüm formatları temizle
                self.clear_all_formatting()

                # Highlighting bilgilerini al
                highlighting_info = self.analyzer.get_syntax_highlighting_info()

                # Her token için highlighting uygula
                self.apply_token_highlighting(highlighting_info, current_text)

                # Analysis completed signal emit et
                self.analysisCompleted.emit(result)

            # Cache'e kaydet
            self.last_highlighted_text = current_text

        except Exception as e:
            print(f"Highlighting error: {e}")
        finally:
            # Cursor pozisyonunu geri yükle
            cursor.setPosition(cursor_position)
            self.setTextCursor(cursor)

            # Highlighting işaretçisini kapat
            self.is_highlighting = False

    def clear_all_formatting(self):
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)

        # Default format
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#000000"))  # Siyah
        cursor.setCharFormat(default_format)

    def apply_token_highlighting(self, highlighting_info, text):
        lines = text.split('\n')

        for token in highlighting_info:
            try:
                line_num = token['line'] - 1  # 0-based index
                column = token['column'] -1
                token_value = token['value']
                token_type = token['type']

                # Satır ve kolon kontrolleri
                if line_num < 0 or line_num >= len(lines):
                    continue

                line_text = lines[line_num]
                if column < 0 or column >= len(line_text):
                    continue

                # Absolute position hesaplama (düzeltilmiş versiyon)
                absolute_position = 0
                for i in range(line_num):
                    absolute_position += len(lines[i]) + 1  # +1 for newline

                absolute_position += column

                # Token uzunluğu kontrolü
                token_length = len(token_value)
                if absolute_position + token_length > len(text):
                    continue

                # Cursor oluştur ve format uygula
                cursor = QTextCursor(self.document())
                cursor.setPosition(absolute_position)
                cursor.setPosition(absolute_position + token_length, QTextCursor.MoveMode.KeepAnchor)
                token_format = self.create_token_format(token_type)
                cursor.setCharFormat(token_format)

            except Exception as e:
                print(f"Token highlighting error: {e}, token: {token}")
                continue

    def create_token_format(self, token_type):
        token_format = QTextCharFormat()

        # Renk belirle
        color = get_token_color(token_type)
        token_format.setForeground(QColor(color))

        # Keyword'ler için bold
        if token_type == 'KEYWORD':
            token_format.setFontWeight(QFont.Weight.Bold)

        # String ve comment'ler için italic
        elif token_type in ['STRING', 'CHARACTER', 'SINGLE_COMMENT', 'MULTI_COMMENT']:
            token_format.setFontItalic(True)

        # Preprocessor için bold + farklı renk
        elif token_type == 'PREPROCESSOR':
            token_format.setFontWeight(QFont.Weight.Bold)

        return token_format