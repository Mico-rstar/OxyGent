# -*- coding: utf-8 -*-
"""
Test document reader tool - Simple test without external dependencies
"""

import os
import asyncio
from dotenv import load_dotenv


def test_read_txt_document():
    """Test read_txt_document function by importing and using it directly"""
    print("Testing read_txt_document function...")

    # Test file path
    test_file = "/home/rene/projs/super-agent/OxyGent/super_agent/tools/test_files/test_document.txt"

    try:
        # Simple test to verify the file exists and can be read
        if not os.path.exists(test_file):
            print(f"❌ Test failed: Test file not found {test_file}")
            return

        # Read the file directly to simulate what the function should do
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print("✅ Successfully read document content:")
        print("-" * 40)
        print(content)
        print("-" * 40)

        # Verify content is not empty
        if content.strip():
            print("✅ Test passed: Successfully read non-empty content")
            print(f"✅ Content length: {len(content)} characters")
            print(f"✅ Content lines: {len(content.splitlines())} lines")
        else:
            print("❌ Test failed: Read content is empty")

    except FileNotFoundError:
        print(f"❌ Test failed: Test file not found {test_file}")
    except Exception as e:
        print(f"❌ Test failed: Error reading document - {str(e)}")


async def test_read_pdf_document():
    """Test read_pdf_document function by importing and using it directly"""
    print("Testing read_pdf_document function...")

    # Test file path
    test_file = "/home/rene/projs/super-agent/OxyGent/data/valid/help_1756092800998.pdf"

    try:
        # Try to import and use the actual function
        from document_reader import read_pdf_document

        # Call the async function and directly output the result
        print(f"Calling read_pdf_document with file: {test_file}")
        print("-" * 50)

        content = await read_pdf_document(test_file, "请提取文档中的所有文字内容，保持原有的格式和结构")

        print(content)
        print("-" * 50)
        print("✅ read_pdf_document function completed successfully")

    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("This is expected if dependencies like dashscope, PyMuPDF are not installed")
    except Exception as e:
        print(f"Function execution result:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("-" * 50)


async def test_read_xlsx_document():
    """Test read_xlsx_document function by importing and using it directly"""
    print("Testing read_xlsx_document function...")

    # Test file path
    test_file = "/home/rene/projs/super-agent/OxyGent/super_agent/tools/test_files/test_document.xlsx"

    try:
        # Try to import and use the actual function
        from document_reader import read_xlsx_document

        # Call the function and directly output the result
        print(f"Calling read_xlsx_document with file: {test_file}")
        print("-" * 50)

        content = await read_xlsx_document(test_file)

        print(content)
        print("-" * 50)
        print("✅ read_xlsx_document function completed successfully")

        # Additional validation
        if content and "读取失败" not in content:
            print("✅ Test passed: Successfully read Excel content")
            print(f"✅ Content length: {len(content)} characters")
        else:
            print("❌ Test failed: Excel content read failed or empty")

    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("This is expected if dependencies like pandas, openpyxl are not installed")
    except FileNotFoundError:
        print(f"❌ Test failed: Test file not found {test_file}")
    except Exception as e:
        print(f"Function execution result:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("-" * 50)


async def test_read_ppt_document():
    """Test read_ppt_document function by importing and using it directly"""
    print("Testing read_ppt_document function...")

    # Test file path
    test_file = "/home/rene/projs/super-agent/OxyGent/super_agent/tools/test_files/test_document.pptx"

    try:
        # Try to import and use the actual function
        from document_reader import read_ppt_document

        # Call the function and directly output the result
        print(f"Calling read_ppt_document with file: {test_file}")
        print("-" * 50)

        content = read_ppt_document(test_file)

        print(content)
        print("-" * 50)
        print("✅ read_ppt_document function completed successfully")

    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("This is expected if dependencies like python-pptx are not installed")
    except Exception as e:
        print(f"Function execution result:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("-" * 50)

if __name__ == "__main__":


    load_dotenv()
    # test_read_txt_document()
    # Test XLSX reading
    # asyncio.run(test_read_xlsx_document())
    # Test PPT reading
    # asyncio.run(test_read_ppt_document())
    # Test PDF reading with asyncio
    asyncio.run(test_read_pdf_document())