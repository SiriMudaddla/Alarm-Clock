 Desktop Alarm Clock

A simple, elegant desktop alarm clock built with Python and Tkinter. Set multiple alarms, snooze or stop them when they ring, switch between dark and light mode, and pick up right where you left off — alarms are saved automatically and reloaded the next time you open the app.


✨ Features


🕐 Live digital clock with the current date

🌙 Dark mode / ☀️ Light mode toggle

➕ Add multiple alarms with hour, minute, and second precision

🔁 Optional "Repeat Daily" alarms that automatically reset each day

🗑️ Delete any alarm from the list

🛑 Stop an alarm while it's ringing

😴 Snooze an alarm for 5 minutes

📊 Live counter showing how many alarms are active

🔔 Alarm notification with sound (5 beeps) and a pop-up message

💾 Alarms persist between sessions, saved to a local alarms.json file




⏰ Alarm Clock                          ☀️ Light Mode

           14:32:07
        Wednesday, June 17, 2026

   📊 2 active alarms (of 3 total)




🛠️ Requirements


Python 3.8+
Tkinter (included with most Python installations)


No external dependencies — just the Python standard library! 🎉


🚀 Getting Started

1️⃣ Clone the repository

bashgit clone https://github.com/your-username/desktop-alarm-clock.git
cd desktop-alarm-clock

2️⃣ Run the app

bashpython alarm_clock.py


🐧 Linux users: if you get a ModuleNotFoundError: No module named 'tkinter', install it first:

bashsudo apt install python3-tk




🎮 Usage


➕ Add an alarm — enter the hour, minute, and second, optionally check "Repeat Daily," then click Add Alarm.

✅ Enable/disable any alarm using its checkbox.

🗑️ Delete an alarm you no longer need.

🔔 When an alarm rings, a pop-up appears with two choices:

🛑 Stop — dismiss the alarm

😴 Snooze 5 min — ring again in 5 minutes



🌗 Toggle Dark/Light mode anytime using the button in the top corner.

💾 Close the app whenever — your alarms will be exactly as you left them next time. ✨



📁 Project Structure

desktop-alarm-clock/
├── alarm_clock.py     # Main application
├── alarms.json         # Auto-generated alarm storage (created on first run)
└── README.md           # You are here 👋


🧩 How It Works

ComponentDescription🖥️ Tkinter GUIRenders the clock, alarm list, and theme switching🧵 ThreadingPlays alarm beeps without freezing the interface📄 JSON storageSaves and loads alarms from alarms.json⏱️ Polling loopChecks the current time every 500ms against all active alarms


🗺️ Roadmap / Ideas


 🎵 Custom alarm sound files (instead of beeps)
 
 ⏳ Configurable snooze duration
 
 🧪 "Test alarm" button to preview the ringing experience

 🌐 Cross-platform native notifications
 
 📱 Label/name each alarm (e.g., "Wake up", "Meeting")



🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or open a pull request. 🙌


🍴 Fork the project


🌿 Create your feature branch (git checkout -b feature/amazing-feature)

💾 Commit your changes (git commit -m 'Add some amazing feature')

🚀 Push to the branch (git push origin feature/amazing-feature)

🔁 Open a pull request



📜 License

This project is licensed under the MIT License — feel free to use, modify, and share it. 💙


⭐ Show Your Support

If you found this project useful, consider giving it a ⭐ on GitHub — it helps a lot!

