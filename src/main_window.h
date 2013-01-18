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

#ifndef YANER_MAIN_WINDOW_H
#define YANER_MAIN_WINDOW_H

#include <QMainWindow>

#include <ui_main_window.h>
#include <yaner.h>

namespace yaner {

class MainWindow: public QMainWindow {
  Q_OBJECT

  public:
    MainWindow();
    virtual ~MainWindow();

  private:
    Ui_main_window ui_;

    QIcon getStockIcon(const QString &name, int fallback=-1);

    DISALLOW_COPY_AND_ASSIGN(MainWindow);
};

} // namespace yaner

#endif /* end of include guard */

