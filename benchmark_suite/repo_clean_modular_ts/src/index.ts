import express, { Request, Response } from "express";
import { z } from "zod";

const app = express();
app.use(express.json());

const UserSchema = z.object({
  username: z.string().min(3),
  email: z.string().email()
});

app.get("/health", (req: Request, res: Response) => {
  res.json({ status: "healthy", timestamp: new Date().toISOString() });
});

app.post("/users", (req: Request, res: Response) => {
  const result = UserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.errors });
  }
  return res.status(201).json({ message: "User registered successfully", user: result.data });
});

export default app;
