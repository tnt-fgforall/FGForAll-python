# FGForAll
This project is just a UI made for easy installation/removal of dlssg-to-fsr3 by Nukem9. I am not taking any credit for the `dlssg-to-fsr3`
project in any way. This project is only developed overnight for my own benefit to easily install/remove the mod to any games I own.
I have an RTX 3090 myself and am frustrated as anyone else.
Do not judge the codebase too much as it was mostly
developed using AI. I had to fix bugs/edge cases to make it work.
The project was built using Vanilla Kotlin/Java and does not even have Maven/Gradle. 
It only requires [GSON](https://mvnrepository.com/artifact/com.google.code.gson/gson) library to be built.

Enjoy! Feel free to not buy me coffee as you can enjoy the coffee yourself! Use the code as you like but don't take credit!

The steps you need to do:
1. Download the [dlss-fg](https://github.com/Nukem9/dlssg-to-fsr3/) mod from the Nexus mods [website](https://www.nexusmods.com/site/mods/738).
2. Extract the downloaded mode to directory `dlss-fg`, all files from the universal mod should be placed under this folder.
3. Download the exe or jar file and place it near the `dlss-fg` directory.
4. Install/Remove the mod for any game you have! It searches for Steam/Epic Games automatically but 
you can also insert the game directory that includes the nvidia dll files. (Drag and drop any file from the relevant directory)
5. Install will create a backup of the dll file that is to be replaced inside a `bak` folder, as you remove the mod,
the backup files will be restored to the original game folder and all the mod files will be deleted.
6. **Beware**: I am not an expert on which games require which folder to be modded, so feel free to just use your own instincts and
use drag & drop feature instead. (Otherwise, it needs to be hardcoded for each game that behaves differently.)

