import logging
import wandb
import client_api


def start_wandb(wandb_key, wandb_project, wandb_name):
    wandb.login(key=wandb_key)
    config_wandb = {
        "learning_rate": 0,
        "optimizer": '',
        "dataset": '',
        "model_architecture": '',
        "batch_size": 0,
        "epochs": 0,
        "num_rounds": 0
    }
    run = wandb.init(project=wandb_project, name=wandb_name, config=config_wandb)

    return run


def data_status_wandb(run=None, labels=None):
    table = wandb.Table(data=labels, columns=["label", "data_size"])
    run.log({'Data Lable Histogram': wandb.plot.bar(table, "label", "data_size", title="Data Size Distribution")})


def client_system_wandb(fl_task_id, client_mac, client_name, gl_model_v, wandb_name, wandb_account, project):
    try:
        cols = ['system.network.sent', 'system.network.recv', 'system.disk.in', '_runtime', 
                'system.proc.memory.rssMB','system.proc.memory.availableMB', 'system.cpu', 
                'system.proc.cpu.threads', 'system.memory', 'system.proc.memory.percent', '_timestamp']
        if client_name!='':
            # check client system resource usage from wandb
            api = wandb.Api()
            runs = api.runs(f"{wandb_account}/{project}")
            for run in runs:
                if run.name == wandb_name:
                    sys_info = run.history(stream="system")
                    sys_info = sys_info[cols]
                    sys_info.rename(columns={
                        "system.network.sent": "network_sent",
                        "system.network.recv": "network_recv",
                        "system.disk.in": "disk",
                        "_runtime": "runtime",
                        "system.proc.memory.rssMB": "memory_rssMB",
                        "system.proc.memory.availableMB": "memory_availableMB",
                        "system.cpu": "cpu",
                        "system.proc.cpu.threads": "cpu_threads",
                        "system.memory": "memory",
                        "system.proc.memory.percent": "memory_percent",
                        "_timestamp": "timestamp",
                    }, inplace=True)

                    # Extract df_row by row
                    for i in range(len(sys_info)):
                        sys_df_row = sys_info.iloc[i].copy()
                        sys_df_row['fl_task_id'] = fl_task_id
                        sys_df_row['client_mac'] = client_mac
                        sys_df_row['client_name'] = client_name
                        sys_df_row['gl_model_v'] = gl_model_v
                        sys_df_row['wandb_name'] = wandb_name

                        sys_df_row_json = sys_df_row.to_json()
                    
                        # send client_system  to client_performance pod
                        client_api.ClientServerAPI(fl_task_id).put_client_system(sys_df_row_json)
                    
                    break
        else:
            pass

        
        
    except Exception as e:
        logging.error(f'wandb system load error: {e}')

