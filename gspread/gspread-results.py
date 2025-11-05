import gspread
import sys
from gspread_formatting import get_user_entered_format, format_cell_range

def read_test_metrics(file_path):
    """
    test.txt 파일을 읽어서 PSNR, SSIM, LPIPS 값을 파싱합니다.
    예시: PSNR : 21.240, SSIM : 0.694, LPIPS : 0.315
    """
    try:
        with open(file_path, 'r') as f:
            line = f.readline().strip()
        parts = line.split(',')
        data = {}
        for part in parts:
            key, val = part.strip().split(':')
            data[key.strip()] = float(val.strip())
        return {
            "PSNR": f"{data.get('PSNR', 0):.3f}",
            "SSIM": f"{data.get('SSIM', 0):.3f}",
            "LPIPS": f"{data.get('LPIPS', 0):.3f}",
        }
    except Exception as e:
        print(f"❌ Error reading test.txt: {e}")
        return {"PSNR": "0.000", "SSIM": "0.000", "LPIPS": "0.000"}

def read_pose_metrics(file_path):
    """
    pose_eval.txt 파일을 읽어서 RPE_trans, RPE_rot, ATE 값을 파싱합니다.
    예시: RPE_trans: 0.026, RPE_rot: 0.035, ATE: 0.003
    """
    try:
        with open(file_path, 'r') as f:
            line = f.readline().strip()
        parts = line.split(',')
        data = {}
        for part in parts:
            key, val = part.strip().split(':')
            data[key.strip()] = float(val.strip())
        return {
            "RPE_trans": f"{data.get('RPE_trans', 0):.3f}",
            "RPE_rot": f"{data.get('RPE_rot', 0):.3f}",
            "ATE": f"{data.get('ATE', 0):.3f}",
        }
    except Exception as e:
        print(f"❌ Error reading pose file: {e}")
        return {"RPE_trans": "0.000", "RPE_rot": "0.000", "ATE": "0.000"}

def copy_format_from_previous_row(sheet, dest_row):
    """이전 행의 셀 서식을 새 행으로 복사합니다."""
    if dest_row <= 2:
        return
    source_row = dest_row - 1
    columns = [chr(i) for i in range(ord('B'), ord('H') + 1)]  # B~H열 복사
    for col in columns:
        source_cell = f'{col}{source_row}'
        dest_cell = f'{col}{dest_row}'
        try:
            fmt = get_user_entered_format(sheet, source_cell)
            if fmt:
                format_cell_range(sheet, dest_cell, fmt)
        except Exception:
            pass

def save_gspread(test_path, pose_path, method_name, sheet_name):
    """Google Sheets에 결과를 업로드합니다."""
    try:
        gc = gspread.service_account(filename='/workdir/gspread/account.json')
        sh = gc.open("EX-results")
        sheet = sh.worksheet(sheet_name)

        # 데이터 읽기
        test_data = read_test_metrics(test_path)
        pose_data = read_pose_metrics(pose_path)

        # 다음 빈 행 찾기
        all_values = sheet.col_values(2)
        row_number = len(all_values) + 1

        copy_format_from_previous_row(sheet, row_number)

        print(f"📤 Uploading to Sheet '{sheet_name}', Row {row_number}...")
        print(f"  Method: {method_name}")
        print(f"  PSNR={test_data['PSNR']}, SSIM={test_data['SSIM']}, LPIPS={test_data['LPIPS']}")
        print(f"  RPE_trans={pose_data['RPE_trans']}, RPE_rot={pose_data['RPE_rot']}, ATE={pose_data['ATE']}")

        # 시트 업데이트
        updates = [
            {'range': f'B{row_number}', 'values': [[method_name]]},
            {'range': f'C{row_number}', 'values': [[test_data["PSNR"]]]},
            {'range': f'D{row_number}', 'values': [[test_data["SSIM"]]]},
            {'range': f'E{row_number}', 'values': [[test_data["LPIPS"]]]},
            {'range': f'F{row_number}', 'values': [[pose_data["RPE_trans"]]]},
            {'range': f'G{row_number}', 'values': [[pose_data["RPE_rot"]]]},
            {'range': f'H{row_number}', 'values': [[pose_data["ATE"]]]},
        ]
        sheet.batch_update(updates)
        print("✅ Data uploaded successfully!")

    except FileNotFoundError:
        print("❌ Error: '/workdir/gspread/account.json' not found.")
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Error: Spreadsheet 'EX-results' not found.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Error: Worksheet '{sheet_name}' not found.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python gspread-results.py <test.txt> <pose_eval.txt> <method_name> <sheet_name>")
        sys.exit(1)

    test_path = sys.argv[1]
    pose_path = sys.argv[2]
    method_name = sys.argv[3]
    sheet_name = sys.argv[4]

    save_gspread(test_path, pose_path, method_name, sheet_name)