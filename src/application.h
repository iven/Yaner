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

#ifndef YANER_APPLICATION_H
#define YANER_APPLICATION_H

#include <QApplication>
#include <QTranslator>

#include <yaner.h>

class QLabel;

namespace yaner {

class Application: public QApplication {
  Q_OBJECT

  public:
    Application(int &argc, char **argv);
    virtual ~Application();

  private:
    QTranslator qt_translator_;
    QTranslator app_translator_;

    QLabel *label_;

    DISALLOW_COPY_AND_ASSIGN(Application);
};

} // namespace yaner

#endif /* end of include guard */

