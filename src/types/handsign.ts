export interface BoundingBox {
  x_min: number
  y_min: number
  x_max: number
  y_max: number
}

export interface TopPrediction {
  label: string
  confidence: number
}

export interface PredictionResponse {
  detected: boolean
  prediction: string | null
  confidence: number
  box: BoundingBox | null
  top_predictions: TopPrediction[]
  frame_width: number
  frame_height: number
}

export interface CameraDetectionResponse extends PredictionResponse {
  confirmed_text: string
  confirmed_prediction: string | null
  threshold_met: boolean
}
