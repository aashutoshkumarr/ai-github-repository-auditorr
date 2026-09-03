package orders

import (
	"context"
	"testing"
)

func TestCreateOrder_Valid(t *testing.T) {
	svc := NewOrderService("postgres://localhost:5432/test")
	ctx := context.Background()

	order, err := svc.CreateOrder(ctx, "usr_123", 5000)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if order.TotalCents != 5000 {
		t.Errorf("expected 5000, got %d", order.TotalCents)
	}
}
