# MP2 實驗與輪換操作指南

作業 PDF 已讀取全部 9 頁（含附錄）；README 已完整閱讀。
開始檢查時 repo 與 `/home/poching2` 的上層均未找到 AGENTS.md。
本文件是建議流程與技術說明，不是兩位同學已完成合作的紀錄。

## 作業要求

目標是縮短資料載入、訓練、測試的整段執行時間，主要輸入為 Diabetes、
Wisconsin Breast Cancer、California Housing。不能省略測試／輸出公式，
或把工作量與模型品質的變化混在實作加速裡。PDF 也介紹兩個影像案例；
本次要求的主要比較是三個 CSV 資料集，沒有據此宣稱影像速度或品質。

PDF 註明截止日為 2026-10-16，要求兩人 pair programming，細粒度輪換
driver（操作、打字）與 observer（觀看、建議、規劃下一步），兩人都應理解全部程式。
需要參加同儕報告與 artifact review。

繳交報告最多 3 頁（參考文獻不計），使用 ACM SIGPLAN 模板，包含優化種類、
假設與適用範圍、效能圖表、成功或失敗原因與反思，以及真實合作段落。
Artifact 是 private Git repo，README 要有建置工具、build/run、baseline 與各項優化
的驗證指令。報告經 HotCRP 繳交，程式提供 repo 連結。
若使用特殊硬體，另需一般 Unix 可重現的版本與特殊硬體版本。
尚未確認課程網站上的額外政策與 HotCRP 開放狀況；此文件只整理附上的 PDF。

## 程式怎麼找公式

1. `benchmark/genetic_benchmark.cpp` 載入 CSV，最後一欄是目標值。
   `train_test_split` 使用固定、依位置平均分散的切分，測試數量是總數的 20% 向下取整；
   不是隨機洗牌。X 與 y 各自用同樣規則切分，所以仍然對齊。
2. 將資料轉為 column-major：同一欄的所有數值連續放在記憶體裡。
3. `symFit` 用 Philox RNG 與固定 seed 驅動每一代。
4. `build_program` 隨機產生公式樹。內部節點是運算，葉節點是特徵或常數。
5. `execute_kernel` 對每一個公式、每一筆資料逆向走訪節點，以 stack 保存中間答案。
   不可更改二元運算的取值順序，例如減法不能顛倒。
6. `compute_metric` 計算訓練品質。`tournament_kernel` 隨機抽幾個候選並挑較好者；
   parsimony penalty 會在競賽時考慮公式長度。
7. `cpp_evolve` 執行 crossover（交換子樹）、subtree mutation（換新子樹）、
   hoist mutation（縮小子樹）、point mutation（改節點）或 reproduction（複製）。
8. 最後依 raw fitness 排序，輸出兩個候選公式與測試 MSE／accuracy。
   排序使用 raw fitness，與競賽使用含長度 penalty 的分數不同；本次比較維持原行為。

## 固定工作量

| 設定 | Diabetes | Cancer | Housing |
|---|---:|---:|---:|
| samples | 442 | 569 | 20640 |
| features | 10 | 30 | 8 |
| train / test | 354 / 88 | 456 / 113 | 16512 / 4128 |
| population | 512 | 16384 | 512 |
| generations 上限 | 16 | 16 | 16 |
| tournament size | 4 | 16 | 4 |
| RNG seed | 2025000000 | 2025 | 2025000000 |
| training metric | MSE | log loss | MSE |
| test metric | MSE | accuracy | MSE |
| parsimony coefficient | 0 | 0.01 | 0 |

其他函數集合、初始化深度、突變比例、資料與 early stopping 條件都保持原版。
原版 stopping criterion = 0；stderr 若出現 early stopping 必須一併檢查。
數值較小的 MSE／log loss 較好，accuracy 較高較好。
兩個候選的公式長度與深度也會保留，避免用較簡單或不同結果的模型冒充等價加速。

## 量測方法

`tools/benchmark.py` 使用 `git archive` 擷取指定 commit，放在獨立且忽略的 source 目錄；
絕不覆蓋工作目錄。每個 variant、每個資料集先暖機一次，再正式量測三次。
一個 benchmark process 完成後才執行下一個，不同 variant 不同時量測。
暖機保留但不納入統計。每次都保留 stdout `.rkt`、stderr、程式內計時、外部 wall time
與移除計時行後的 SHA-256。保留 metadata 的 commit、編譯旗標及資料／原始碼雜湊。

主要報告正式量測的中位數，另提供 min–max、平均與 sample standard deviation（n−1）。
加速比 = baseline 中位數 / variant 中位數。三次僅用來初步觀察變動，不宣稱統計顯著性。
相同 seed 的重跑可看時間變動，但不能當作跨 seed 的模型品質研究。
VM 可能受到宿主機與背景程序影響；結果只代表本次環境。

程式內的 `CLOCK_MONOTONIC` 計時涵蓋載入、訓練、測試及公式輸出，
但停在 final_programs 的釋放前。外部 wall time 也包含 process 啟動與最後清理；
兩種都保存，不混用來計算同一組加速比。

perf 無法存取時保留錯誤，不自行調整 VM 的系統安全設定；改用 gprof。
gprof 的 `-pg`／`-g` 執行只用於找熱點，不能納入正式時間表。
正確性以完整輸出比對、stack 邊界測試及 sanitizer／Valgrind 記錄檢查。

## Driver／observer 的小步驟

| 小步驟 | driver 操作 | observer 核對 | 完成後 |
|---|---|---|---|
| 環境與 Git | 查看 cwd、hostname、status、remote | 是否正確 VM／private remote，有無既有改動 | 交換角色 |
| baseline | build 原版，跑一組資料的量測 | 旗標、seed、population、generations、輸出完整性 | 交換角色 |
| profiling | 保存 perf 或 gprof 結果 | 區分 self time 與累積時間，不能相加重疊 call graph 百分比 | 交換角色 |
| 一項優化 | 只修改一個原因明確的熱點 | 算子順序、空／滿 stack、是否改了資料或 RNG | 交換角色 |
| 驗證 | 執行測試與完整資料量測 | 公式／品質／錯誤訊息，是否有記憶體錯誤 | 交換角色 |
| commit | review diff，使用簡單英文 commit | 訊息是否只描述實際改動 | 交換角色 |
| 整理 | 由原始紀錄產出比較表與圖 | 暖機排除、中位數、比較基準與限制 | 交換角色 |

你與 Christine 的實際合作段落：**待你們提供實際日期、輪換與討論情況後撰寫**。
可在每步記下日期、誰當 driver／observer、討論的假設與測試結果；不要預填完成紀錄。
