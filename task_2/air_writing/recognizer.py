# $1 gesture recognizer

import math as math
import time as time


class Point:

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Rectangle:

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class Unistroke:

    def __init__(self, name, points):
        self.name = name
        self.points = resample(points, NUMPOINTS)
        self.radians = indicativeAngle(self.points)
        self.points = rotateBy(self.points, -self.radians)
        self.points = scaleTo(self.points, SQUARE_SIZE)
        self.points = translateTo(self.points, ORIGIN)
        self.vector = vectorize(self.points)


class Result:

    def __init__(self, name, score, ms):
        self.name = name
        self.score = score
        self.Time = ms


NUM_OF_UNISTROKES = 16
NUMPOINTS = 64
SQUARE_SIZE = 250.0
ORIGIN = Point(0, 0)
DIAGONAL = math.sqrt(SQUARE_SIZE * SQUARE_SIZE + SQUARE_SIZE * SQUARE_SIZE)
HALF_DIAGONAL = 0.5 * DIAGONAL
ANGLE_RANGE = math.radians(45.0)
ANGLE_PRECISION = math.radians(2.0)
PHI = 0.5 * (-1.0 + math.sqrt(5.0))


class DollarRecognizer:

    def __init__(self):
        self.unistrokes = []

    def recognize(self, points, useProtractor):

        t0 = time.time()
        candidate = Unistroke("", points)

        u = -1
        b = math.inf

        for i in range(len(self.unistrokes)):

            d = 0.0

            if useProtractor:
                d = optimalCosineDistance(
                    self.unistrokes[i].vector, candidate.vector)
            else:
                d = distanceAtBestAngle(
                    candidate.points, self.unistrokes[i], -ANGLE_RANGE, ANGLE_RANGE, ANGLE_PRECISION)

            if d < b:
                b = d
                u = i

        t1 = time.time()

        if u == -1:
            return Result("No match", 0.0, (t1 - t0) * 1000.0)
        else:
            if useProtractor:
                return Result(self.unistrokes[u].name, 1.0 - b, (t1 - t0) * 1000.0)
            else:
                return Result(self.unistrokes[u].name, 1.0 - b / HALF_DIAGONAL, (t1 - t0) * 1000.0)

    def addGesture(self, name, points):

        self.unistrokes.append(Unistroke(name, points))
        num = 0

        for i in range(len(self.unistrokes)):
            if self.unistrokes[i].name == name:
                num += 1
        return num

    def deleteUserGestures(self):

        self.unistrokes = self.unistrokes[:NUM_OF_UNISTROKES]
        return NUM_OF_UNISTROKES


def resample(points, n):

    interval = pathLength(points) / (n - 1)
    distance_so_far = 0.0
    newpoints = [points[0]]

    i = 1
    while i < len(points):
        d = distance(points[i - 1], points[i])
        if (distance_so_far + d) >= interval:
            qx = points[i - 1].x + ((interval - distance_so_far) / d) * \
                (points[i].x - points[i - 1].x)
            qy = points[i - 1].y + ((interval - distance_so_far) / d) * \
                (points[i].y - points[i - 1].y)
            q = Point(qx, qy)
            newpoints.append(q)
            points.insert(i, q)
            distance_so_far = 0.0
        else:
            distance_so_far += d
        i += 1

    if len(newpoints) == n - 1:
        newpoints.append(
            Point(points[len(points) - 1].x, points[len(points) - 1].y))

    return newpoints


def indicativeAngle(points):

    c = centroid(points)
    return math.atan2(c.y - points[0].y, c.x - points[0].x)


def rotateBy(points, radians):

    c = centroid(points)
    cos = math.cos(radians)
    sin = math.sin(radians)
    newpoints = []

    for i in range(len(points)):
        qx = (points[i].x - c.x) * cos - (points[i].y - c.y) * sin + c.x
        qy = (points[i].x - c.x) * sin + (points[i].y - c.y) * cos + c.y
        newpoints.append(Point(qx, qy))

    return newpoints


def scaleTo(points, size):

    b = boundingBox(points)
    newpoints = []

    for i in range(len(points)):
        qx = points[i].x * (size / b.width)
        qy = points[i].y * (size / b.height)
        newpoints.append(Point(qx, qy))

    return newpoints


def translateTo(points, pt):

    c = centroid(points)
    newpoints = []

    for i in range(len(points)):
        qx = points[i].x + pt.x - c.x
        qy = points[i].y + pt.y - c.y
        newpoints.append(Point(qx, qy))

    return newpoints


def vectorize(points):

    total = 0.0
    vector = []

    for i in range(len(points)):
        vector.append(points[i].x)
        vector.append(points[i].y)
        total += points[i].x * points[i].x + points[i].y * points[i].y

    magnitude = math.sqrt(total)

    for i in range(len(vector)):
        vector[i] /= magnitude

    return vector


def optimalCosineDistance(v1, v2):

    a = 0.0
    b = 0.0

    for i in range(0, len(v1), 2):
        a += v1[i] * v2[i] + v1[i + 1] * v2[i + 1]
        b += v1[i] * v2[i + 1] - v1[i + 1] * v2[i]

    angle = math.atan(b / a)
    return math.acos(a * math.cos(angle) + b * math.sin(angle))


def distanceAtBestAngle(points, t, a, b, threshold):

    x1 = PHI * a + (1.0 - PHI) * b
    f1 = distanceAtAngle(points, t, x1)
    x2 = (1.0 - PHI) * a + PHI * b
    f2 = distanceAtAngle(points, t, x2)

    while abs(b - a) > threshold:
        if f1 < f2:
            b = x2
            x2 = x1
            f2 = f1
            x1 = PHI * a + (1.0 - PHI) * b
            f1 = distanceAtAngle(points, t, x1)
        else:
            a = x1
            x1 = x2
            f1 = f2
            x2 = (1.0 - PHI) * a + PHI * b
            f2 = distanceAtAngle(points, t, x2)

    return min(f1, f2)


def distanceAtAngle(points, t, radians):
    newpoints = rotateBy(points, radians)
    return pathDistance(newpoints, t.points)


def centroid(points):

    x = 0.0
    y = 0.0

    for i in range(len(points)):
        x += points[i].x
        y += points[i].y

    x /= len(points)
    y /= len(points)

    return Point(x, y)


def boundingBox(points):

    minX = math.inf
    maxX = -math.inf
    minY = math.inf
    maxY = -math.inf

    for i in range(len(points)):
        minX = min(minX, points[i].x)
        minY = min(minY, points[i].y)
        maxX = max(maxX, points[i].x)
        maxY = max(maxY, points[i].y)

    return Rectangle(minX, minY, maxX - minX, maxY - minY)


def pathDistance(pts1, pts2):

    d = 0.0

    for i in range(len(pts1)):
        d += distance(pts1[i], pts2[i])

    return d / len(pts1)


def pathLength(points):

    d = 0.0

    for i in range(1, len(points)):
        d += distance(points[i - 1], points[i])

    return d


def distance(p1, p2):

    dx = p2.x - p1.x
    dy = p2.y - p1.y

    return math.sqrt(dx * dx + dy * dy)
