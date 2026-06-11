# RaccoonBot OpenVLA MuJoCo Client

이 폴더는 Lecture19 PDF의 Step 4 client-side 실행 방식에 맞춘 로컬 MuJoCo client이다.

## 포함 파일

- `openvla_multicolor_client.py`: MuJoCo client rollout
- `batch_eval_openvla_client.py`: 색상/seed별 batch rollout
- `openvla_multicolor_client_real_robot.py`: 실제 RaccoonBot 연결 실험용
- `raccoon_env.py`: MuJoCo RaccoonBot 실행 환경
- `Raccoon_colored_cylinder.xml`, `RaccoonBot_S.xml`: MuJoCo scene/model
- `assets/`: robot mesh assets
- `requirements.txt`: client dependencies

## 설치

```bash
cd /data/biy/client
pip install -r requirements.txt
```

## PDF 방식 실행

서버에서 OpenVLA server를 먼저 실행한다.

```bash
cd /data/biy/Raccoonbot_Openvla/openvla
CUDA_VISIBLE_DEVICES=0 python openvla_server.py \
  --model_path /path/to/openvla-run-or-adapter-merged-model \
  --default-unnorm-key raccoon_pick_place \
  --host 0.0.0.0 \
  --port 8000 \
  --device cuda
```

클라이언트 PC에서 서버 port가 직접 열려 있지 않으면 SSH tunnel을 연다.

```bash
ssh -L 8000:127.0.0.1:8000 root@qlak315.iptime.org -p 23000
```

터널을 연 터미널은 닫지 않는다. 다른 터미널에서 연결을 확인한다.

```bash
curl http://127.0.0.1:8000
```

`{"detail":"Not Found"}`가 나오면 FastAPI server에 연결된 것이다.

MuJoCo client 실행:

```bash
cd /data/biy/client
python openvla_multicolor_client.py \
  --server_url http://127.0.0.1:8000 \
  --xml_path Raccoon_colored_cylinder.xml \
  --target_color red \
  --use_viewer
```

## VLA-only 평가 주의

다음 flag들은 client-side 보조 제어이므로, VLA-only 성능 평가에서는 켜지 않는다.

- `--assist_xy_alignment_before_close`
- `--gate_close_by_xy`
- `--preclose_min_z_when_xy_bad`
- `--latch_gripper_after_close`
- `--post_close_clamp_negative_z`
- `--post_close_lift_controller`
- `--post_close_keep_xy`
- `--use_action_smoothing`

