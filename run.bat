@echo off
setlocal
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
:menu
cls
echo ===============================================
echo Synthetic Head and Eye Motion Pipeline
echo ===============================================
echo 1. Generate textures
echo 2. Create Blender head and eye rig
echo 3. Render left gaze
echo 4. Render right gaze
echo 5. Generate complete motion
echo 6. Generate hero stills
echo 7. Run UV seam audit
echo 8. Run all tests
echo 9. Exit
set /p choice=Choose an option:
if "%choice%"=="1" python src\generate_textures.py --count 8 --size 4096 --out_dir textures\uv_maps\
if "%choice%"=="2" blender -b --python src\setup_blender_rig.py
if "%choice%"=="3" blender -b blend_files\synthetic_head_rig.blend -P src\run_pipeline.py -- --input Left --texture textures\uv_maps\subject_01_albedo.png --output outputs\videos\output_left.mp4
if "%choice%"=="4" blender -b blend_files\synthetic_head_rig.blend -P src\run_pipeline.py -- --input Right --texture textures\uv_maps\subject_01_albedo.png --output outputs\videos\output_right.mp4
if "%choice%"=="5" blender -b blend_files\synthetic_head_rig.blend -P src\run_pipeline.py -- --input "Generate Motion" --texture textures\uv_maps\subject_01_albedo.png --output outputs\videos\output_generate_motion.mp4
if "%choice%"=="6" blender -b blend_files\synthetic_head_rig.blend -P src\run_pipeline.py -- --batch_stills textures\uv_maps --output outputs\renders
if "%choice%"=="7" python src\uv_seam_audit.py textures\uv_maps\subject_01_albedo.png --output outputs\reports
if "%choice%"=="8" python -m unittest discover -s tests -v
if "%choice%"=="9" exit /b 0
pause
goto menu
