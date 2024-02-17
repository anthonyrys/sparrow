from scripts.utils.bezier import bezier_presets, get_bezier_point

class Easing(object):
    def __init__(self):
        self.tasks = []

    def create(self, attr, to, to_time, to_bezier='ease_out', dt=0, count=0):
        task = {}

        task['attr'] = attr
        task['to'] = [getattr(attr[0], attr[1]), to]

        task['time'] = [0, to_time]
        task['bezier'] = bezier_presets[to_bezier]
        task['dt'] = dt

        task['count'] = count

        del_tasks = []
        for t in self.tasks:
            if t['attr'] == attr:
                del_tasks.append(t)

        for t in del_tasks:
            self.tasks.remove(t)
            
        self.tasks.append(task)

    def update(self, game):
        del_tasks = []
        for task in self.tasks:
            if game.delta_time == 0 and task['dt'] == 0:
                continue

            if task['count'] > 0:
                task['count'] -= 1 * (game.delta_time if task['dt'] == 0 else game.raw_delta_time)
                continue

            abs_prog = task['time'][0] / task['time'][1]

            d = task['to'][1] - task['to'][0]
            v =  task['to'][0] + d * get_bezier_point(abs_prog, *task['bezier'])
            setattr(task['attr'][0], task['attr'][1], v)

            task['time'][0] += 1 * (game.delta_time if task['dt'] == 0 else game.raw_delta_time)

            if task['time'][0] > task['time'][1]:
                task['time'][0] = task['time'][1]

                setattr(task['attr'][0], task['attr'][1], task['to'][1])
                del_tasks.append(task)

        for task in del_tasks:
            self.tasks.remove(task)
