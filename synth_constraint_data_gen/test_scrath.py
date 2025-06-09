from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem, Job, Task
from csp_cop_src.solvers.solve_job_shop_scheduling import solve_job_shop_scheduling
from csp_cop_src.nl_probem_generators.job_shop_scheduling_make_nl import generate_jobshop_prompt
from csp_cop_src.problem_generators.job_shop_scheduling_generator import JobShopProblemCOPGenerator, JobShopProblemCSPGenerator

from csp_cop_src.solvers.solve_job_shop_scheduling import solve_job_shop_scheduling

problem = JobShopSchedulingProblem(
    problem_id="test",
    jobs=[Job(job_id=0, tasks=[Task(machine_id=0, duration=2), Task(machine_id=1, duration=3)]),
            Job(job_id=1, tasks=[Task(machine_id=1, duration=2), Task(machine_id=0, duration=3)])],
    makespan_target=5)
solution = solve_job_shop_scheduling(problem)
prompt = generate_jobshop_prompt(problem.to_dict())

js_generator = JobShopProblemCSPGenerator(
    min_num_jobs=2,
    max_num_jobs=4,
    min_num_machines=2,
    max_num_machines=5,
    min_tasks_per_job=2,
    max_tasks_per_job=4,
    min_task_time=1,
    max_task_time=15,
    satisfiable_makespan=True,
)
new_probems = js_generator.generate_problems(num_samples=100, prefix='js_cop')
q_1 = new_probems[0]
soln_1 = solve_job_shop_scheduling(q_1)
q_2 = new_probems[1]
soln_2 = solve_job_shop_scheduling(q_2)
breakpoint()
print(solution)









