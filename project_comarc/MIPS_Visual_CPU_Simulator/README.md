# MIPS Factorial & nCr Visual CPU Architecture Simulator

โครงงาน Computer Architecture: จำลองการประมวลผล MIPS Assembly ด้วย Python 3.10+ และ Tkinter โดยไม่ใช้ API หรือเซิร์ฟเวอร์

## เริ่มต้น (Windows / VS Code)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python main.py --selftest
python main.py
```

หาก PowerShell ไม่อนุญาต activate ให้ใช้ `\.venv\Scripts\python.exe` แทน `python` ในคำสั่งทั้งหมด

## ใช้งาน GUI

1. เลือก Factorial หรือ nCr และเลือก optimized / factorial_based
2. กรอก n และ r (r ใช้เฉพาะ nCr)
3. กด Load แล้ว Step ทีละคำสั่ง หรือ Run/Turbo เพื่อคำนวณต่อเนื่อง
4. เปิดแท็บ Instructions, Registers, Memory, Trace และ Performance
5. กด Compare เพื่อเปรียบเทียบจำนวนคำสั่งของ nCr สองวิธี

## โครงสร้าง

- `main.py` — จุดเริ่มโปรแกรม
- `programs/` — MIPS Assembly สามโปรแกรม
- `simulator/` — Contract, Assembler, ISA, Memory, CPU
- `integration/` — Controller, Runner, Selftest
- `interface/` — GUI และ Datapath Visualization
- `reference/` — คำตอบ Python สำหรับตรวจสอบเท่านั้น
- `tests/` — Automated tests
- `tools/` — Independent interpreter และเครื่องมือตรวจ
- `docs/` — ISA, Flowcharts, Register convention
- `references/original_cpuSimV7/` — ต้นฉบับอาจารย์ ไม่แก้ไข

## ข้อจำกัด

เป็น **functional single-cycle simulator** ไม่ใช่ Pipeline ไม่มี Branch Delay Slot และไม่มี Clock Timing Model. CPU execute จาก parsed `Instr` (Machine Code ที่ encode ใช้เพื่อแสดงผลและเก็บใน memory). Optimized nCr อาจ trap `OVERFLOW` ในบางอินพุต n≥18. GUI Performance ปัจจุบันแสดงตารางเปรียบเทียบ (ยังไม่มีกราฟ Matplotlib). ยังไม่ได้ยืนยันการทำงานของ GUI บน Windows จริงและยังไม่ได้ทำ regression ครบกับ cpuSimV7.

## GitHub

```powershell
git init
git add .
git commit -m "Initial MIPS visual CPU simulator"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

หาก repository มีอยู่แล้ว ให้ `git clone URL` และคัดลอกไฟล์ลงใน repository นั้นแทนการ `git init` ซ้ำ
