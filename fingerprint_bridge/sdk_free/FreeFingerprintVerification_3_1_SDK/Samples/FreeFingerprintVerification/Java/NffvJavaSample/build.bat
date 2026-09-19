set batpath=%~dp0
@mkdir %batpath%bin
@mkdir %batpath%bin\img
copy %batpath%img\logo.png %batpath%bin\img
copy %batpath%flatlaf.jar %batpath%..\..\..\..\Bin\Win64_x64
javac -d %batpath%bin -source 1.8 -target 1.8 -cp %batpath%..\..\..\..\Bin\Win64_x64\Nffv.jar;%batpath%flatlaf.jar %batpath%src\NffvSample\*.java
jar -cmvf %batpath%src\manifest.txt %batpath%..\..\..\..\Bin\Win64_x64\NffvSample.jar -C %batpath%bin NffvSample -C %batpath%bin img
copy %batpath%NffvSample.html %batpath%..\..\..\..\Bin\Win64_x64\
copy %batpath%NffvSample.bat %batpath%..\..\..\..\Bin\Win64_x64\
copy %batpath%NffvSample-wow64.bat %batpath%..\..\..\..\Bin\Win64_x64\
