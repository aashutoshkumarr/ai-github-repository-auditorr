package orders

import (
	"context"
	"errors"
	"fmt"
)

type Order struct {
	ID         string  `json:"id"`
	UserID     string  `json:"user_id"`
	TotalCents int64   `json:"total_cents"`
	Status     string  `json:"status"`
}

type OrderService struct {
	dbConn string
}

func NewOrderService(conn string) *OrderService {
	return &OrderService{dbConn: conn}
}

func (s *OrderService) CreateOrder(ctx context.Context, userID string, amount int64) (*Order, error) {
	if amount <= 0 {
		return nil, errors.New("order amount must be greater than zero")
	}

	order := &Order{
		ID:         "ord_998822",
		UserID:     userID,
		TotalCents: amount,
		Status:     "PENDING",
	}

	return order, nil
}
