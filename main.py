#!C:\Users\SPECTRE\Uni_Notes\Bahar2\ProgramlamaDilleri\LabCodeProject\labcode_venv\Scripts\python.exe

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QLabel,
                             QFileDialog, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from highlighter_text_edit import *


class LabCodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_stylesheet()

    def initUI(self):
        # Ana pencere ayarları
        self.setWindowTitle('Real-Time C Syntax Highlighter')
        self.setGeometry(100, 100, 1200, 800)
        
        # Merkezi widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        
        # Menu bar oluştur
        self.create_menu_bar()
        
        # Splitter ile editor ve info paneli
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sol panel - Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Editor başlığı
        editor_label = QLabel("C Code Editor")
        editor_label.setObjectName("title_label")
        editor_layout.addWidget(editor_label)
        
        # Text editor
        self.text_editor = CustomSyntaxTextEditor()
        # Analysis completed signal'ını bağla
        self.text_editor.analysisCompleted.connect(self.update_analysis_results)
        self.text_editor.textChanged.connect(self.update_status)
        self.text_editor.setObjectName("main_editor")
        self.text_editor.setFont(QFont('Consolas', 12))
        self.text_editor.setPlaceholderText("C kodunuzu buraya yazın...\n\n// örnek:\n#include <stdio.h>\n\nint main() {\n    printf(\"Hello World!\");\n    return 0;\n}")
        editor_layout.addWidget(self.text_editor)

        splitter.addWidget(editor_widget)
        
        # Sağ panel - Bilgi paneli
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Bilgi paneli başlığı
        info_label = QLabel("Syntax Analysis Info")
        info_label.setObjectName("title_label")
        info_layout.addWidget(info_label)
        
        # Token bilgi alanı
        self.token_info = QTextEdit()
        self.token_info.setMaximumHeight(200)
        self.token_info.setFont(QFont('Consolas', 10))
        self.token_info.setPlaceholderText("Token bilgileri burada görünecek...")
        self.token_info.setReadOnly(True)
        info_layout.addWidget(QLabel("Detected Tokens:"))
        info_layout.addWidget(self.token_info)
        
        # Parse tree bilgi alanı
        self.parse_info = QTextEdit()
        self.parse_info.setFont(QFont('Consolas', 10))
        self.parse_info.setPlaceholderText("Parse tree bilgileri burada görünecek...")
        self.parse_info.setReadOnly(True)
        info_layout.addWidget(QLabel("Parse Tree:"))
        info_layout.addWidget(self.parse_info)
        
        # Durum bilgisi
        self.status_info = QLabel("Ready - Real-time analysis active")
        self.status_info.setObjectName("status_label")
        info_layout.addWidget(QLabel("Status:"))
        info_layout.addWidget(self.status_info)
        
        splitter.addWidget(info_widget)
        
        # Splitter boyutları (sol paneli daha geniş yap)
        splitter.setSizes([800, 400])
        
        main_layout.addWidget(splitter)
        
        # Alt durum çubuğu
        self.create_status_bar()

    def create_menu_bar(self):
        # Menü çubuğu
        menubar = self.menuBar()
        
        # File menüsü
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('&Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menüsü
        view_menu = menubar.addMenu('&View')
        
        clear_action = QAction('&Clear All', self)
        clear_action.triggered.connect(self.clear_all)
        view_menu.addAction(clear_action)
    
    def create_status_bar(self):
        self.statusBar().showMessage('Ready - Real-time C Syntax Highlighter')

    def update_status(self):
        """Text değiştiğinde Status Bar güncelle"""
        text_length = len(self.text_editor.toPlainText())
        line_count = self.text_editor.document().blockCount()

        # Status güncelle
        if text_length > 0:
            # Status bar güncelle
            self.statusBar().showMessage(f'Lines: {line_count} | Characters: {text_length} | Real-time analysis active')
            self.update_status_info("Analyzing code...")
        else:
            self.update_status_info("Ready for new code")
            self.statusBar().showMessage('Ready - Real-time C Syntax Highlighter')
            self.clear_analysis_info()

    def update_analysis_results(self, result):
        """Analiz sonuçlarını güncelle"""
        if result['success']:
            # Token info güncelle
            if hasattr(self, 'token_info'):
                self.token_info.setText(result['token_info'])

            # Parse info güncelle
            if hasattr(self, 'parse_info'):
                self.parse_info.setText(result['parse_info'])

            # Hata varsa göster
            if result['errors']:
                self.update_status_info(f"Analysis complete with {len(result['errors'])} errors")
                error_text = "Errors:\n" + "\n".join(result['errors'])
                if hasattr(self, 'parse_info'):
                    self.parse_info.setText(error_text)
            else:
                self.update_status_info("Analysis complete - No errors")
        else:
            # Analiz başarısız
            if hasattr(self, 'token_info'):
                self.token_info.setText("Analysis failed")
            if hasattr(self, 'parse_info'):
                self.parse_info.setText("Analysis failed")
            self.update_status_info("Analysis failed")

    def clear_analysis_info(self):
        """Analiz bilgilerini temizle"""
        self.token_info.clear()
        self.parse_info.clear()
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open C File', '', 'C Files (*.c);;All Files (*)')
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_editor.setText(content)
                self.update_status_info(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to open file: {str(e)}')
    
    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save C File', '', 'C Files (*.c);;All Files (*)')
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_editor.toPlainText())
                self.update_status_info(f"Saved: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save file: {str(e)}')
    
    def clear_all(self):
        """Tüm içeriği temizle"""
        self.text_editor.clear()
        self.clear_analysis_info()
        self.update_status_info("Cleared - Ready for new code")
    
    def update_status_info(self, message):
        """Durum bilgisini güncelle"""
        self.status_info.setText(message)
    
    def load_stylesheet(self):
        """Stylesheet dosyasını yükle"""
        try:
            # Stylesheet dosyasını bul
            style_file = '../labCode_v1/dark_stylesheet.qss'
            
            # Eğer dosya yoksa varsayılan stil kullan
            if os.path.exists(style_file):
                with open(style_file, 'r', encoding='utf-8') as file:
                    stylesheet = file.read()
                self.setStyleSheet(stylesheet)
            else:
                # Varsayılan minimal dark theme
                self.setStyleSheet("""
                    QMainWindow { background-color: #1e1e1e; color: #cccccc; }
                    QTextEdit { 
                        background-color: #1e1e1e; 
                        color: #d4d4d4; 
                        border: 1px solid #3c3c3c; 
                        border-radius: 4px; 
                        padding: 8px; 
                    }
                    QLabel { color: #cccccc; }
                    QMenuBar { background-color: #2d2d30; color: #cccccc; }
                    QStatusBar { background-color: #007acc; color: #ffffff; }
                """)
        except Exception as e:
            print(f"Stylesheet yüklenemedi: {e}")
            # Hata durumunda varsayılan stil

def main():
    app = QApplication(sys.argv)
    
    # Uygulama stili
    app.setStyle('Fusion')
    
    window = LabCodeApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()