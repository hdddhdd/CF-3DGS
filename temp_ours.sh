#!/bin/bash
# 데이터셋 리스트
# "Ballroom"
datasets=("Family" "Museum" "Ballroom")
# 각 데이터셋에 대해 실행
SHEET_NAME="PC2"       # 구글 시트 내 워크시트 이름
QP_LEVEL="qp37"        # 모델 버전
TYPE="tanks"          # 데이터 유형
for dataset in "${datasets[@]}"
do
    echo "=========================================="
    echo "Processing: $dataset"
    echo "=========================================="

    EXP_NAME="Ours_trustmap095"
    MODEL_PATH="./output/${EXP_NAME}/${QP_LEVEL}_${dataset}"
    MODEL_FILE="${MODEL_PATH}/chkpnt/ep00_init.pth"

    # 평가 실행
    python run_cf3dgs.py -s ./data/compress-o/tnt/qp37/$dataset/ --mode train --data_type $TYPE \
        --scene_name "$dataset" \
        --qp_level "$QP_LEVEL"  \
        --trust_momentum 0.95  \
        --expname "${EXP_NAME}" \
        --ours false
        
    python run_cf3dgs.py --source ./data/compress-x/tnt/$dataset --mode eval_pose --data_type $TYPE --model_path "$MODEL_FILE"
    python run_cf3dgs.py --source ./data/compress-x/tnt/$dataset --mode eval_nvs  --data_type $TYPE --model_path "$MODEL_FILE"

    # 에러 체크
    if [ $? -ne 0 ]; then
        echo "⚠️ Error occurred during processing of $dataset"
    fi

    # 업로드 경로
    TEST_PATH="${MODEL_PATH}/test/test.txt"
    POSE_PATH="${MODEL_PATH}/pose/pose_eval.txt"

    if [ -f "$TEST_PATH" ]; then
        echo "📤 Uploading $dataset results to Google Sheet (${SHEET_NAME})..."
        python gspread/gspread-results.py \
            "$TEST_PATH" \
            "$POSE_PATH" \
            "$MODEL_PATH" \
            "$SHEET_NAME"
    else
        echo "⚠️ No test.txt found for ${dataset}, skipping upload."
    fi

    echo "✅ Completed: $dataset"
    echo ""
done

echo "🎯 All datasets processed and uploaded!"