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

#ifndef YANER_YANER_H
#define YANER_YANER_H

#include <QtDebug>

namespace yaner {

#define DISALLOW_COPY_AND_ASSIGN(TypeName) \
    TypeName(const TypeName&); \
    void operator=(const TypeName&)

// Logging
#define LOGGING_FORMAT __FILE__ << __LINE__ << __FUNCTION__ << "|"

#define QDEBUG    qDebug()    << "[DEBUG]"    << LOGGING_FORMAT
#define QWARNING  qWarning()  << "[WARNING]"  << LOGGING_FORMAT
#define QCRITICAL qCritical() << "[CRITICAL]" << LOGGING_FORMAT
#define QFATAL    qFatal()    << "[FATAL]"    << LOGGING_FORMAT

} // namespace yaner

#endif /* end of include guard */

