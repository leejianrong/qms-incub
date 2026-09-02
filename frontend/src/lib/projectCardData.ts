// Shared by ProjectsDashboard.svelte and Favourites.svelte, which both
// need the same project-list-to-cards pipeline: fetch every project, fill
// in its todos (real backend todos once classified, or the create-wizard's
// stashed plan for a project that isn't — wizardPlan.ts, ADR-0012), and
// build each card's view-model (projectCards.ts). Kept out of both
// components so the fetch-and-assemble logic can't drift between them.
import { getProject, listProcessSteps, listProjects, type Project, type TodoItem } from "./api";
import { buildProjectCard, type ProjectCardViewModel } from "./projectCards";
import { loadWizardPlan, wizardPlanToSteps, wizardPlanToTodos } from "./wizardPlan";

export interface ProjectCardsResult {
  cards: ProjectCardViewModel[];
  allTodos: TodoItem[];
}

export async function loadProjectCards(apiBase: string): Promise<ProjectCardsResult> {
  const [projects, steps] = await Promise.all([listProjects(apiBase), listProcessSteps(apiBase)]);
  const details = await Promise.all(
    projects.map(async (project: Project) => {
      if (project.risk_tier === null) {
        const plan = loadWizardPlan(project.id);
        if (plan) {
          return {
            project,
            todos: wizardPlanToTodos(project.id, plan),
            steps: wizardPlanToSteps(plan),
            hasWizardPlan: true,
          };
        }
        return { project, todos: [] as TodoItem[], steps, hasWizardPlan: false };
      }
      try {
        const detail = await getProject(apiBase, project.id);
        return { project, todos: detail.todos, steps, hasWizardPlan: false };
      } catch {
        return { project, todos: [] as TodoItem[], steps, hasWizardPlan: false };
      }
    }),
  );
  return {
    cards: details.map((d) => buildProjectCard(d.project, d.todos, d.steps, d.hasWizardPlan)),
    allTodos: details.flatMap((d) => d.todos),
  };
}
