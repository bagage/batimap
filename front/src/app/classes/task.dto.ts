export class TaskDTO {
    // eslint-disable-next-line @typescript-eslint/naming-convention, no-underscore-dangle, id-blacklist, id-match
    task_id!: string;
    name!: string;
    args!: string[];
    running!: boolean;
}
