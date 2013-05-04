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

#include "main_window.h"

#include <QtWidgets>

using namespace yaner;

QIcon MainWindow::getStockIcon(const QString &name, int fallback) {
  QIcon icon = QIcon::fromTheme(name);
  if (icon.isNull() && (fallback >= 0)) {
    icon = style()->standardIcon(QStyle::StandardPixmap(fallback), 0, this);
  }

  return icon;
}

MainWindow::MainWindow() {
  QDEBUG << "Constructing the main window.";

  ui_.setupUi(this);

  ui_.action_task_new->setIcon(getStockIcon("document-new", QStyle::SP_DesktopIcon));
  ui_.action_task_start->setIcon(getStockIcon("media-playback-start", QStyle::SP_MediaPlay));
  ui_.action_task_pause->setIcon(getStockIcon("media-playback-pause", QStyle::SP_MediaPause));
  ui_.action_task_delete->setIcon(getStockIcon("edit-delete", QStyle::SP_TrashIcon));
  ui_.action_properties->setIcon(getStockIcon("preferences-system"));
  ui_.action_about->setIcon(getStockIcon("help-about"));
  ui_.action_quit->setIcon(getStockIcon("application-exit"));

  connect(ui_.action_quit, SIGNAL(triggered()), qApp, SLOT(quit()));

  QDEBUG << "Main window constructed.";
}

MainWindow::~MainWindow() {
}

