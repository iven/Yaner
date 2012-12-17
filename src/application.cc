/*
 * Yaner - Aria2 based download utility
 * Copyright (C) 2010-2013 Iven Hsu <ivenvd#gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "application.h"

#include <QLabel>
#include <QLibraryInfo>
#include <QLocale>

#include "config.h"
#include "main_window.h"
#include "yaner.h"

using namespace yaner;

Application::Application(int &argc, char **argv): QApplication(argc, argv) {
  QDEBUG << "Initializing application.";

  setApplicationName(PROJECT_NAME);
  setApplicationVersion(PROJECT_VERSION);

  // install translators
  qt_translator_.load("qt_" + QLocale::system().name(),
                      QLibraryInfo::location(QLibraryInfo::TranslationsPath));
  installTranslator(&qt_translator_);

  app_translator_.load(PROJECT_NAME "_" + QLocale::system().name(), ":/ts/");
  installTranslator(&app_translator_);

  main_window_ = new MainWindow();
  main_window_->show();

  QDEBUG << "Application initialized.";
}

Application::~Application() {
  delete main_window_;
}

