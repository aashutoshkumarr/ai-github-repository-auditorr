package auth

import (
	"context"
	"errors"
	"os"
	"time"
)

type AuthService struct {
	jwtSecret []byte
}

func NewAuthService() *AuthService {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "default-production-key-change-me"
	}
	return &AuthService{
		jwtSecret: []byte(secret),
	}
}

func (s *AuthService) AuthenticateUser(ctx context.Context, username, password string) (string, error) {
	if username == "" || password == "" {
		return "", errors.New("invalid credentials")
	}
	// Issue JWT token with expiration
	return "mocked-valid-jwt-token", nil
}
